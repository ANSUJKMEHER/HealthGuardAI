"""
HealthGuard AI — Reporter Agent
Verifies system recovery and generates post-mortem incident reports.
"""

import time
from typing import Dict, Any, Optional

import structlog

from app.config import settings
from app.llm.base import LLMProvider
from app.monitoring.system_monitor import SystemMonitor
from app.database.session import get_db
from app.database.repositories import IncidentRepository, AgentActionRepository
from app.monitoring.metrics import (
    INCIDENTS_RESOLVED, INCIDENTS_FAILED, ACTIVE_INCIDENTS, AGENT_ACTIONS
)

logger = structlog.get_logger("ReporterAgent")


class ReporterAgent:
    """
    Verifies system recovery after a fix and generates incident reports.
    Updates MTTR metrics and incident statistics.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def verify_and_report(self, system: SystemMonitor, incident_id: int,
                          diagnosis: Dict[str, Any], action: str) -> Optional[str]:
        """
        Wait for system stabilization, verify recovery, and generate report.

        Args:
            system: The monitored system to check
            incident_id: Database ID of the incident
            diagnosis: Diagnosis data from DiagnosticianAgent
            action: The fix action that was taken

        Returns:
            Generated report string if recovered, None otherwise
        """
        logger.info("verifying_recovery", incident_id=incident_id)
        AGENT_ACTIONS.labels(agent="ReporterAgent", action_type="VERIFY").inc()

        # Wait for system to stabilize
        time.sleep(3)

        metrics = system.get_metrics()
        is_recovered = (
            metrics["cpu_percent"] < settings.cpu_threshold and
            metrics["memory_mb"] < settings.memory_threshold_mb
        )

        # Generate report
        incident_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "failure_type": diagnosis.get("root_cause", "Unknown"),
            "diagnosis": diagnosis,
            "action_taken": action,
            "recovered": is_recovered,
        }

        report = self.llm.generate_report(incident_data)

        # Update database
        with get_db() as db:
            repo = IncidentRepository(db)
            repo.verify_recovery(incident_id, is_recovered, report)

            action_repo = AgentActionRepository(db)
            action_repo.log(
                incident_id=incident_id,
                agent_name="ReporterAgent",
                action_type="VERIFY",
                details={"recovered": is_recovered, "post_fix_metrics": metrics},
            )

        # Update Prometheus metrics
        if is_recovered:
            INCIDENTS_RESOLVED.labels(
                failure_type=diagnosis.get("root_cause", "unknown"),
                action_taken=action
            ).inc()
            logger.info("incident_resolved",
                         incident_id=incident_id,
                         root_cause=diagnosis.get("root_cause"))
        else:
            INCIDENTS_FAILED.labels(
                failure_type=diagnosis.get("root_cause", "unknown")
            ).inc()
            logger.error("recovery_failed",
                          incident_id=incident_id,
                          post_fix_metrics=metrics)

        return report if is_recovered else None
