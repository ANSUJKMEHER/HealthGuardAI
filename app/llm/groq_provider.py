"""
HealthGuard AI — Groq LLM Provider (FREE API)
Real AI integration using Groq's API with Llama3-70b.
Free tier: 30 requests/minute, no credit card required.
Sign up at: https://console.groq.com
"""

import json
import time
from typing import Dict, Any

import structlog

from app.llm.base import LLMProvider
from app.llm.prompts import (
    DIAGNOSTICIAN_SYSTEM_PROMPT, DIAGNOSTICIAN_USER_PROMPT,
    REPORTER_SYSTEM_PROMPT, REPORTER_USER_PROMPT,
)
from app.monitoring.metrics import LLM_REQUESTS, LLM_LATENCY

logger = structlog.get_logger(__name__)


class GroqProvider(LLMProvider):
    """
    Real LLM provider using Groq's free API.
    Uses Llama3-70b for fast, high-quality inference.
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model
        logger.info("llm_provider_initialized", provider="groq", model=model)

    def analyze_anomaly(self, metrics: Dict[str, Any], logs: list) -> Dict[str, Any]:
        """Send metrics + logs to Groq LLM for real AI diagnosis."""
        # Format logs for the prompt
        logs_text = "\n".join([
            f"[{log.get('timestamp', '?')}] [{log.get('level', 'INFO')}] {log.get('message', '')}"
            for log in logs
        ]) if logs else "No recent log entries."

        user_prompt = DIAGNOSTICIAN_USER_PROMPT.format(
            cpu_percent=metrics.get("cpu_percent", 0),
            memory_mb=metrics.get("memory_mb", 0),
            response_time_ms=metrics.get("response_time_ms", 0),
            error_rate_percent=metrics.get("error_rate_percent", 0),
            logs_text=logs_text,
        )

        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": DIAGNOSTICIAN_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for deterministic diagnosis
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            duration = time.time() - start_time
            LLM_LATENCY.observe(duration)
            LLM_REQUESTS.labels(provider="groq", status="success").inc()

            # Parse the response
            content = response.choices[0].message.content
            diagnosis = json.loads(content)

            logger.info("llm_diagnosis_complete",
                        provider="groq",
                        root_cause=diagnosis.get("root_cause"),
                        confidence=diagnosis.get("confidence"),
                        duration_s=round(duration, 2))

            # Validate required keys
            required_keys = ["thought_process", "root_cause", "confidence", "recommended_action"]
            for key in required_keys:
                if key not in diagnosis:
                    raise ValueError(f"Missing required key in LLM response: {key}")

            # Clamp confidence to valid range
            diagnosis["confidence"] = max(0.0, min(1.0, float(diagnosis["confidence"])))

            return diagnosis

        except Exception as e:
            duration = time.time() - start_time
            LLM_REQUESTS.labels(provider="groq", status="error").inc()
            logger.error("llm_diagnosis_failed", provider="groq", error=str(e), duration_s=round(duration, 2))
            raise

    def generate_report(self, incident_data: Dict[str, Any]) -> str:
        """Generate a post-mortem report using the LLM."""
        user_prompt = REPORTER_USER_PROMPT.format(
            failure_type=incident_data.get("failure_type", "Unknown"),
            root_cause=incident_data.get("diagnosis", {}).get("root_cause", "Unknown"),
            confidence=incident_data.get("diagnosis", {}).get("confidence", "N/A"),
            thought_process=incident_data.get("diagnosis", {}).get("thought_process", "N/A"),
            action_taken=incident_data.get("action_taken", "None"),
            outcome="System recovered — metrics returned to normal" if incident_data.get("recovered") else "Recovery failed — manual intervention needed",
            timestamp=incident_data.get("timestamp", "Unknown"),
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": REPORTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )

            LLM_REQUESTS.labels(provider="groq", status="success").inc()
            return response.choices[0].message.content

        except Exception as e:
            LLM_REQUESTS.labels(provider="groq", status="error").inc()
            logger.error("llm_report_failed", error=str(e))
            # Return a basic report as fallback
            return f"""# 🚨 Incident Report: {incident_data.get('failure_type', 'Unknown')}
**Status:** {'RESOLVED' if incident_data.get('recovered') else 'UNRESOLVED'}
**Action Taken:** {incident_data.get('action_taken', 'None')}
*Report generation failed — this is a fallback summary.*"""
