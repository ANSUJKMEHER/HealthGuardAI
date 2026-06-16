"""
HealthGuard AI — Fixer Agent
Executes safe autonomous fixes based on diagnosis results.
Implements safety guardrails: action allowlist and confidence threshold.
"""

import time
from typing import Dict, Any

import structlog

from app.config import settings
from app.monitoring.system_monitor import SystemMonitor
from app.database.session import get_db
from app.database.repositories import IncidentRepository, AgentActionRepository
from app.monitoring.metrics import FIX_DURATION, AGENT_ACTIONS

logger = structlog.get_logger("FixerAgent")


class FixerAgent:
    """
    Executes autonomous fixes with safety guardrails.
    Only performs actions from the SAFE_ACTIONS allowlist.
    Requires minimum confidence threshold before acting.
    """

    # Actions that are approved for autonomous execution
    SAFE_ACTIONS = ["RESTART_SERVICE", "CLEAR_CACHE", "HEAL_REMOTE_SYSTEM"]

    def __init__(self, system: SystemMonitor):
        self.system = system

    def execute_fix(self, diagnosis: Dict[str, Any], incident_id: int) -> bool:
        """
        Execute a fix based on diagnosis.

        Safety checks:
        1. Confidence must exceed threshold (default 0.8)
        2. Action must be in the SAFE_ACTIONS allowlist

        Returns True if fix was executed, False if blocked.
        """
        action = diagnosis.get("recommended_action")
        confidence = diagnosis.get("confidence", 0.0)

        AGENT_ACTIONS.labels(agent="FixerAgent", action_type="FIX_ATTEMPT").inc()

        # Safety Check 1: Confidence threshold
        if confidence < settings.confidence_threshold:
            logger.warning("fix_blocked_low_confidence",
                           incident_id=incident_id,
                           confidence=confidence,
                           threshold=settings.confidence_threshold)
            return False

        # Safety Check 2: Action allowlist
        if action not in self.SAFE_ACTIONS:
            logger.warning("fix_blocked_unsafe_action",
                           incident_id=incident_id,
                           action=action,
                           allowed=self.SAFE_ACTIONS)
            return False

        # Execute the fix
        logger.info("executing_fix",
                     incident_id=incident_id,
                     action=action,
                     confidence=confidence)

        start_time = time.time()
        success = False

        if action == "RESTART_SERVICE":
            success = self.system.restart_service()
        elif action == "CLEAR_CACHE":
            success = self.system.clear_cache()
        elif action == "HEAL_REMOTE_SYSTEM":
            success = self.system.heal_target()

        duration_ms = (time.time() - start_time) * 1000
        FIX_DURATION.observe(duration_ms / 1000)

        # Record in database
        with get_db() as db:
            repo = IncidentRepository(db)
            repo.log_fix_action(incident_id, action, duration_ms)

            action_repo = AgentActionRepository(db)
            action_repo.log(
                incident_id=incident_id,
                agent_name="FixerAgent",
                action_type="FIX_EXECUTE",
                details={"action": action, "success": success},
                duration_ms=duration_ms,
            )

        if success:
            logger.info("fix_executed",
                         incident_id=incident_id,
                         action=action,
                         duration_ms=round(duration_ms, 1))
        else:
            logger.error("fix_failed",
                          incident_id=incident_id,
                          action=action)

        return success
