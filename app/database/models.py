"""
HealthGuard AI — SQLAlchemy ORM Models
Production-grade schema with proper types, timestamps, and relationships.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    func
)
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Incident(Base):
    """
    Represents a detected infrastructure incident and its lifecycle.
    Tracks: detection → diagnosis → fix attempt → verification.
    """
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Detection
    failure_type = Column(String(100), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="DETECTED", index=True)
    # DETECTED → DIAGNOSED → FIX_ATTEMPTED → RESOLVED / FAILED

    # Diagnosis (populated by DiagnosticianAgent)
    root_cause = Column(String(200))
    confidence = Column(Float)
    thought_process = Column(Text)
    diagnosis_json = Column(JSON)

    # Fix (populated by FixerAgent)
    action_taken = Column(String(100))
    fix_duration_ms = Column(Float)

    # Verification (populated by ReporterAgent)
    recovery_verified = Column(Boolean, default=False)
    report = Column(Text)

    # Metrics snapshot at time of detection
    cpu_at_detection = Column(Float)
    memory_at_detection = Column(Float)
    latency_at_detection = Column(Float)
    error_rate_at_detection = Column(Float)

    def to_dict(self):
        """Serialize to dictionary for API responses."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "failure_type": self.failure_type,
            "status": self.status,
            "root_cause": self.root_cause,
            "confidence": self.confidence,
            "thought_process": self.thought_process,
            "action_taken": self.action_taken,
            "fix_duration_ms": self.fix_duration_ms,
            "recovery_verified": self.recovery_verified,
            "report": self.report,
            "metrics_snapshot": {
                "cpu_percent": self.cpu_at_detection,
                "memory_mb": self.memory_at_detection,
                "latency_ms": self.latency_at_detection,
                "error_rate": self.error_rate_at_detection,
            }
        }


class MetricSnapshot(Base):
    """
    Time-series metric data point from the monitored system.
    Used for historical analysis and Grafana dashboard queries.
    """
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         nullable=False, index=True)
    cpu_percent = Column(Float, nullable=False)
    memory_mb = Column(Float, nullable=False)
    error_rate_percent = Column(Float, default=0.0)
    response_time_ms = Column(Float, default=0.0)
    is_anomaly = Column(Boolean, default=False)


class AgentAction(Base):
    """
    Audit log of every action taken by any agent.
    Provides full traceability for incident post-mortems.
    """
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    incident_id = Column(Integer, index=True)
    agent_name = Column(String(50), nullable=False)  # MonitorAgent, DiagnosticianAgent, etc.
    action_type = Column(String(50), nullable=False)  # DETECT, DIAGNOSE, FIX, VERIFY, REPORT
    details = Column(JSON)
    duration_ms = Column(Float)
