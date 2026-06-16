"""
HealthGuard AI — Fallback LLM Provider (Rule-Based)
Deterministic rule-based diagnosis used when no LLM API is available.
This is the original logic preserved as a reliable fallback.
"""

import time
from typing import Dict, Any

import structlog

from app.llm.base import LLMProvider
from app.monitoring.metrics import LLM_REQUESTS

logger = structlog.get_logger(__name__)


class FallbackProvider(LLMProvider):
    """
    Rule-based diagnosis provider. No external API needed.
    Uses deterministic if-else logic for 100% reliable demos.
    """

    def analyze_anomaly(self, metrics: Dict[str, Any], logs: list) -> Dict[str, Any]:
        """Diagnose anomaly using rule-based logic."""
        cpu = metrics.get("cpu_percent", 0)
        mem = metrics.get("memory_mb", 0)
        latency = metrics.get("response_time_ms", 0)
        error_rate = metrics.get("error_rate_percent", 0)
        logs_text = " ".join([l.get("message", "") for l in logs]) if logs else ""

        LLM_REQUESTS.labels(provider="fallback", status="success").inc()

        # ── Memory Leak (Critical) ───────────────────────────
        if "OutOfMemoryError" in logs_text or "OOM" in logs_text:
            return {
                "thought_process": "CRITICAL: Logs contain OutOfMemoryError. Application heap is exhausted. "
                                   "Immediate restart required to restore service availability.",
                "root_cause": "Critical Memory Leak (OOM)",
                "confidence": 0.99,
                "recommended_action": "RESTART_SERVICE"
            }

        if mem > 100:
            return {
                "thought_process": f"Memory usage is abnormally high ({mem}MB > 100MB threshold). "
                                   f"Progressive memory leak detected in the application process. "
                                   f"Triggering remote system heal to clear leaked memory.",
                "root_cause": "Application Memory Leak",
                "confidence": 0.98,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }

        if mem > 300 and "Garbage collection" in logs_text:
            return {
                "thought_process": "Memory is at warning level and GC is thrashing. "
                                   "Clearing cache should relieve heap pressure without a full restart.",
                "root_cause": "High Heap Usage (Cache Bloat)",
                "confidence": 0.85,
                "recommended_action": "CLEAR_CACHE"
            }

        # ── CPU Spike ────────────────────────────────────────
        if cpu > 50:
            return {
                "thought_process": f"CPU usage sustained above 50% ({cpu}%). "
                                   f"Indicates a process stuck in a computation loop or infinite recursion. "
                                   f"Healing the remote system to kill the runaway thread.",
                "root_cause": "CPU Saturation (Runaway Process)",
                "confidence": 0.96,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }

        # ── Server Crash (HTTP 500) ──────────────────────────
        if "HTTP 500" in logs_text or "HTTP 503" in logs_text or "Connection refused" in logs_text:
            return {
                "thought_process": "CRITICAL: Detected HTTP 5xx errors from the monitored endpoint. "
                                   "The remote service is failing. Triggering self-healing protocols.",
                "root_cause": "Remote Service Crash (HTTP 5xx)",
                "confidence": 0.95,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }

        if error_rate > 10:
            return {
                "thought_process": "Error rate spiked above 10%. Connection refusals detected. "
                                   "Likely a transient network partition or service hang.",
                "root_cause": "Database Connection Pool Exhaustion",
                "confidence": 0.92,
                "recommended_action": "RESTART_SERVICE"
            }

        # ── High Latency ─────────────────────────────────────
        if latency > 5000:
            return {
                "thought_process": f"Response time is CRITICAL ({latency}ms). "
                                   f"Exceeds normal lag — indicates database query timeout or hung connections.",
                "root_cause": "Database Connection Timeout",
                "confidence": 0.93,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }

        if latency > 1000:
            return {
                "thought_process": f"Response time elevated ({latency}ms). "
                                   f"Service is slow but CPU/errors are normal. External dependency lag.",
                "root_cause": "High Service Latency",
                "confidence": 0.90,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }

        # ── Rate Limiting ────────────────────────────────────
        if "HTTP 429" in logs_text or "Too Many Requests" in logs_text:
            return {
                "thought_process": "HTTP 429 rate limit responses detected. "
                                   "Traffic spike or misconfigured rate limits.",
                "root_cause": "Rate Limit Exceeded",
                "confidence": 0.94,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }

        # ── Network Partition ────────────────────────────────
        if "Service Unavailable" in logs_text or "Network Partition" in logs_text:
            return {
                "thought_process": "HTTP 503 Service Unavailable detected. "
                                   "Network partition, service overload, or infrastructure failure.",
                "root_cause": "Network Partition / Service Unavailable",
                "confidence": 0.91,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }

        # ── Normal ───────────────────────────────────────────
        return {
            "thought_process": "All metrics within normal operating parameters. No intervention needed.",
            "root_cause": "None",
            "confidence": 1.0,
            "recommended_action": "WAIT"
        }

    def generate_report(self, incident_data: Dict[str, Any]) -> str:
        """Generate a template-based incident report."""
        diagnosis = incident_data.get("diagnosis", {})
        return f"""# 🚨 INCIDENT REPORT: {incident_data.get('failure_type', 'Unknown')}

**Date:** {incident_data.get('timestamp', 'Unknown')}
**Status:** {'RESOLVED ✅' if incident_data.get('recovered') else 'UNRESOLVED ❌'}

## 🔍 Root Cause Analysis
**Diagnosis:** {diagnosis.get('root_cause', 'Unknown')}
**Confidence:** {diagnosis.get('confidence', 'N/A')}
**AI Reasoning:** {diagnosis.get('thought_process', 'N/A')}

## 🛠️ Remediation
**Action Taken:** {incident_data.get('action_taken', 'None')}
**Result:** {'System metrics verified — returned to normal levels.' if incident_data.get('recovered') else 'Recovery verification failed. Manual intervention may be required.'}

## 📋 Recommendations
- Investigate recent deployments that may have introduced the regression
- Review application code for resource leaks in the affected module
- Consider adding automated canary deployments to catch issues earlier
"""
