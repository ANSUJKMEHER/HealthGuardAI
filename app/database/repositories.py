"""
HealthGuard AI — Data Access Layer (Repository Pattern)
Clean abstraction over database operations. No raw SQL anywhere.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.database.models import Incident, MetricSnapshot, AgentAction

import structlog

logger = structlog.get_logger(__name__)


class IncidentRepository:
    """Handles all incident-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, failure_type: str, metrics: Dict[str, Any] = None) -> Incident:
        """Log a new incident when an anomaly is detected."""
        incident = Incident(
            failure_type=failure_type,
            status="DETECTED",
            cpu_at_detection=metrics.get("cpu_percent") if metrics else None,
            memory_at_detection=metrics.get("memory_mb") if metrics else None,
            latency_at_detection=metrics.get("response_time_ms") if metrics else None,
            error_rate_at_detection=metrics.get("error_rate_percent") if metrics else None,
        )
        self.db.add(incident)
        self.db.flush()  # Get the ID without committing
        logger.info("incident_created", incident_id=incident.id, failure_type=failure_type)
        return incident

    def update_diagnosis(self, incident_id: int, root_cause: str, confidence: float,
                         thought_process: str, diagnosis_json: dict):
        """Update incident with diagnosis results."""
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if incident:
            incident.root_cause = root_cause
            incident.confidence = confidence
            incident.thought_process = thought_process
            incident.diagnosis_json = diagnosis_json
            incident.failure_type = root_cause  # Use specific diagnosis as failure type
            incident.status = "DIAGNOSED"
            incident.updated_at = datetime.now(timezone.utc)

    def log_fix_action(self, incident_id: int, action: str, duration_ms: float = None):
        """Record fix attempt on an incident."""
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if incident:
            incident.action_taken = action
            incident.fix_duration_ms = duration_ms
            incident.status = "FIX_ATTEMPTED"
            incident.updated_at = datetime.now(timezone.utc)

    def verify_recovery(self, incident_id: int, recovered: bool, report: str = None):
        """Mark incident as resolved or failed after verification."""
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if incident:
            incident.recovery_verified = recovered
            incident.status = "RESOLVED" if recovered else "FAILED"
            incident.report = report
            incident.updated_at = datetime.now(timezone.utc)

    def get_recent(self, limit: int = 10) -> List[Incident]:
        """Get most recent incidents."""
        return (
            self.db.query(Incident)
            .order_by(desc(Incident.id))
            .limit(limit)
            .all()
        )

    def get_all(self) -> List[Incident]:
        """Get all incidents for export."""
        return self.db.query(Incident).order_by(desc(Incident.id)).all()

    def get_resolved_count(self, failure_type: str) -> int:
        """Count past resolved incidents of the same type (for agent memory)."""
        return (
            self.db.query(func.count(Incident.id))
            .filter(Incident.failure_type == failure_type, Incident.status == "RESOLVED")
            .scalar() or 0
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get incident statistics for the dashboard."""
        total = self.db.query(func.count(Incident.id)).scalar() or 0
        resolved = self.db.query(func.count(Incident.id)).filter(Incident.status == "RESOLVED").scalar() or 0
        failed = self.db.query(func.count(Incident.id)).filter(Incident.status == "FAILED").scalar() or 0

        # Average fix time for resolved incidents
        avg_fix_time = (
            self.db.query(func.avg(Incident.fix_duration_ms))
            .filter(Incident.status == "RESOLVED", Incident.fix_duration_ms.isnot(None))
            .scalar()
        )

        return {
            "total_incidents": total,
            "resolved": resolved,
            "failed": failed,
            "success_rate": round((resolved / total * 100), 1) if total > 0 else 100.0,
            "avg_fix_time_ms": round(avg_fix_time, 1) if avg_fix_time else 0,
        }


class MetricsRepository:
    """Handles metric snapshot storage and time-series queries."""

    def __init__(self, db: Session):
        self.db = db

    def record(self, cpu: float, memory: float, error_rate: float,
               response_time: float, is_anomaly: bool = False):
        """Store a metric data point."""
        snapshot = MetricSnapshot(
            cpu_percent=cpu,
            memory_mb=memory,
            error_rate_percent=error_rate,
            response_time_ms=response_time,
            is_anomaly=is_anomaly,
        )
        self.db.add(snapshot)

    def get_recent(self, limit: int = 60) -> List[MetricSnapshot]:
        """Get recent metric snapshots for dashboard charts."""
        return (
            self.db.query(MetricSnapshot)
            .order_by(desc(MetricSnapshot.recorded_at))
            .limit(limit)
            .all()
        )


class AgentActionRepository:
    """Audit trail for all agent actions."""

    def __init__(self, db: Session):
        self.db = db

    def log(self, incident_id: int, agent_name: str, action_type: str,
            details: dict = None, duration_ms: float = None):
        """Record an agent action for audit trail."""
        action = AgentAction(
            incident_id=incident_id,
            agent_name=agent_name,
            action_type=action_type,
            details=details,
            duration_ms=duration_ms,
        )
        self.db.add(action)
        logger.info("agent_action_logged",
                     agent=agent_name, action=action_type,
                     incident_id=incident_id)

    def get_for_incident(self, incident_id: int) -> List[AgentAction]:
        """Get all agent actions for a specific incident."""
        return (
            self.db.query(AgentAction)
            .filter(AgentAction.incident_id == incident_id)
            .order_by(AgentAction.timestamp)
            .all()
        )
