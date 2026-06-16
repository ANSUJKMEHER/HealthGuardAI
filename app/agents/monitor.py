"""
HealthGuard AI — Monitor Agent
Observes system metrics and detects anomalies using configurable thresholds.
"""

import time
from typing import Dict, Any, Optional

import structlog

from app.config import settings
from app.monitoring.system_monitor import SystemMonitor
from app.monitoring.metrics import INCIDENTS_DETECTED, AGENT_ACTIONS

logger = structlog.get_logger("MonitorAgent")


class MonitorAgent:
    """
    Continuously observes the target system and detects anomalies.
    Uses configurable thresholds from settings.
    """

    def __init__(self, system: SystemMonitor):
        self.system = system

    def observe(self) -> Optional[Dict[str, Any]]:
        """
        Check current metrics against thresholds.
        Returns anomaly context if detected, None otherwise.
        """
        metrics = self.system.get_metrics()
        logs = self.system.get_recent_logs()

        is_cpu_high = metrics["cpu_percent"] > settings.cpu_threshold
        is_mem_high = metrics["memory_mb"] > settings.memory_threshold_mb
        is_error_high = metrics["error_rate_percent"] > settings.error_rate_threshold
        is_latency_high = metrics["response_time_ms"] > settings.latency_threshold_ms

        if is_cpu_high or is_mem_high or is_error_high or is_latency_high:
            # Determine anomaly type for metrics labeling
            anomaly_type = "unknown"
            if is_mem_high:
                anomaly_type = "memory"
            elif is_cpu_high:
                anomaly_type = "cpu"
            elif is_error_high:
                anomaly_type = "error_rate"
            elif is_latency_high:
                anomaly_type = "latency"

            INCIDENTS_DETECTED.labels(failure_type=anomaly_type).inc()
            AGENT_ACTIONS.labels(agent="MonitorAgent", action_type="DETECT").inc()

            logger.warning("anomaly_detected",
                           cpu=metrics["cpu_percent"],
                           memory_mb=metrics["memory_mb"],
                           error_rate=metrics["error_rate_percent"],
                           latency_ms=metrics["response_time_ms"],
                           anomaly_type=anomaly_type)

            return {
                "metrics": metrics,
                "logs": logs,
                "anomaly_type": anomaly_type,
                "detected_at": time.time(),
            }

        return None
