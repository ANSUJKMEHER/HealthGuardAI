"""
HealthGuard AI — Core Engine (Orchestrator)
The main HealthGuard system that coordinates all agents in the detect-diagnose-fix-report loop.
"""

import time
import threading
from typing import Optional, Callable, List, Dict, Any

import structlog

from app.config import settings
from app.monitoring.system_monitor import SystemMonitor
from app.agents.monitor import MonitorAgent
from app.agents.diagnostician import DiagnosticianAgent
from app.agents.fixer import FixerAgent
from app.agents.reporter import ReporterAgent
from app.llm.base import LLMProvider
from app.llm.fallback_provider import FallbackProvider
from app.database.session import get_db, init_db
from app.database.repositories import IncidentRepository
from app.monitoring.metrics import ACTIVE_INCIDENTS

logger = structlog.get_logger("HealthGuardEngine")


def create_llm_provider() -> LLMProvider:
    """Factory function to create the configured LLM provider."""
    if settings.llm_provider == "groq" and settings.groq_api_key:
        try:
            from app.llm.groq_provider import GroqProvider
            return GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)
        except Exception as e:
            logger.warning("groq_init_failed_falling_back", error=str(e))
            return FallbackProvider()
    else:
        logger.info("using_fallback_llm_provider")
        return FallbackProvider()


class HealthGuardEngine:
    """
    Core orchestrator that runs the autonomous healing loop.
    Coordinates: Monitor → Diagnostician → Fixer → Reporter
    """

    def __init__(self):
        # Initialize database
        init_db()

        # Create LLM provider
        self.llm_provider = create_llm_provider()

        # Create system monitor
        self.system_monitor = SystemMonitor()

        # Create agents
        self.monitor = MonitorAgent(self.system_monitor)
        self.diagnostician = DiagnosticianAgent(self.llm_provider)
        self.fixer = FixerAgent(self.system_monitor)
        self.reporter = ReporterAgent(self.llm_provider)

        # State
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # SSE event subscribers
        self._event_listeners: List[Callable] = []

        logger.info("engine_initialized",
                     llm_provider=settings.llm_provider,
                     target_url=settings.target_url)

    def add_event_listener(self, callback: Callable):
        """Register a callback for real-time SSE events."""
        self._event_listeners.append(callback)

    def _emit_event(self, event_type: str, data: dict):
        """Emit an event to all SSE listeners."""
        event = {"type": event_type, "data": data, "timestamp": time.time()}
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception:
                pass

    def start(self):
        """Start the monitoring system and agent loop."""
        if self._running:
            logger.warning("engine_already_running")
            return

        self._running = True
        self.system_monitor.start()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        self._emit_event("system_started", {"status": "running"})
        logger.info("engine_started", target_url=self.system_monitor.target_url)

    def stop(self):
        """Stop the monitoring system."""
        logger.info("engine_stopping")
        self._running = False
        self.system_monitor.stop()
        if self._thread:
            self._thread.join(timeout=10)

        self._emit_event("system_stopped", {"status": "stopped"})
        logger.info("engine_stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    def _run_loop(self):
        """Main agent loop: detect → diagnose → fix → report."""
        while self._running:
            try:
                # 1. MONITOR — Check for anomalies
                anomaly_context = self.monitor.observe()

                if anomaly_context:
                    self._emit_event("anomaly_detected", anomaly_context["metrics"])

                    # Create incident in DB
                    with get_db() as db:
                        repo = IncidentRepository(db)
                        incident = repo.create(
                            "ANOMALY_DETECTED",
                            metrics=anomaly_context["metrics"]
                        )
                        incident_id = incident.id

                    ACTIVE_INCIDENTS.inc()

                    # 2. DIAGNOSE — Analyze root cause
                    diagnosis = self.diagnostician.diagnose(anomaly_context, incident_id)
                    self._emit_event("diagnosis_complete", {
                        "incident_id": incident_id,
                        "root_cause": diagnosis["root_cause"],
                        "confidence": diagnosis["confidence"],
                        "thought_process": diagnosis["thought_process"],
                    })

                    # 3. FIX — Execute autonomous fix
                    fix_executed = self.fixer.execute_fix(diagnosis, incident_id)

                    if fix_executed:
                        self._emit_event("fix_applied", {
                            "incident_id": incident_id,
                            "action": diagnosis["recommended_action"],
                        })

                        # 4. REPORT — Verify and document
                        report = self.reporter.verify_and_report(
                            self.system_monitor,
                            incident_id,
                            diagnosis,
                            diagnosis["recommended_action"],
                        )

                        self._emit_event("incident_resolved", {
                            "incident_id": incident_id,
                            "resolved": report is not None,
                        })

                        # Cool-down after fix
                        time.sleep(5)

                    ACTIVE_INCIDENTS.dec()

            except Exception as e:
                logger.error("engine_loop_error", error=str(e), exc_info=True)
                self._emit_event("error", {"message": str(e)})

            time.sleep(settings.poll_interval_seconds)
