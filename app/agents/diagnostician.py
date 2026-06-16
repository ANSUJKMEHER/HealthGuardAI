"""
HealthGuard AI — Diagnostician Agent
Analyzes anomalies using LLM reasoning (or fallback rules) to determine root cause.
Includes memory recall from past resolved incidents.
"""

import time
from typing import Dict, Any

import structlog

from app.llm.base import LLMProvider
from app.database.session import get_db
from app.database.repositories import IncidentRepository, AgentActionRepository
from app.monitoring.metrics import (
    DIAGNOSIS_DURATION, DIAGNOSIS_CONFIDENCE, AGENT_ACTIONS
)

logger = structlog.get_logger("DiagnosticianAgent")


class DiagnosticianAgent:
    """
    Uses LLM reasoning to diagnose the root cause of detected anomalies.
    Has memory — checks past resolved incidents for confidence boosting.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def diagnose(self, context: Dict[str, Any], incident_id: int) -> Dict[str, Any]:
        """
        Analyze anomaly context and produce a diagnosis.

        Args:
            context: Anomaly data from MonitorAgent (metrics + logs)
            incident_id: Database ID of the current incident

        Returns:
            Diagnosis dict with root_cause, confidence, recommended_action
        """
        logger.info("diagnosis_started", incident_id=incident_id)
        start_time = time.time()

        AGENT_ACTIONS.labels(agent="DiagnosticianAgent", action_type="DIAGNOSE").inc()

        # 1. LLM Analysis
        try:
            diagnosis = self.llm.analyze_anomaly(context["metrics"], context["logs"])
        except Exception as e:
            logger.error("llm_analysis_failed", error=str(e), incident_id=incident_id)
            # If LLM fails, return a safe default
            diagnosis = {
                "thought_process": f"LLM analysis failed ({str(e)}). Unable to diagnose automatically.",
                "root_cause": "Unknown (LLM Unavailable)",
                "confidence": 0.5,
                "recommended_action": "WAIT"
            }

        duration_ms = (time.time() - start_time) * 1000
        DIAGNOSIS_DURATION.observe(duration_ms / 1000)
        DIAGNOSIS_CONFIDENCE.observe(diagnosis.get("confidence", 0))

        # 2. Memory Recall — check past resolved incidents
        with get_db() as db:
            repo = IncidentRepository(db)
            past_success = repo.get_resolved_count(diagnosis["root_cause"])

            if past_success > 0:
                diagnosis["thought_process"] += (
                    f" [MEMORY] Recalled {past_success} past successful resolutions "
                    f"for this exact issue type. Confidence boosted."
                )
                diagnosis["confidence"] = min(0.99, diagnosis["confidence"] + 0.05)
                logger.info("memory_recall",
                            incident_id=incident_id,
                            past_resolutions=past_success)

            # 3. Persist diagnosis to database
            repo.update_diagnosis(
                incident_id=incident_id,
                root_cause=diagnosis["root_cause"],
                confidence=diagnosis["confidence"],
                thought_process=diagnosis["thought_process"],
                diagnosis_json=diagnosis,
            )

            # 4. Audit trail
            action_repo = AgentActionRepository(db)
            action_repo.log(
                incident_id=incident_id,
                agent_name="DiagnosticianAgent",
                action_type="DIAGNOSE",
                details=diagnosis,
                duration_ms=duration_ms,
            )

        logger.info("diagnosis_complete",
                     incident_id=incident_id,
                     root_cause=diagnosis["root_cause"],
                     confidence=diagnosis["confidence"],
                     duration_ms=round(duration_ms, 1))

        return diagnosis
