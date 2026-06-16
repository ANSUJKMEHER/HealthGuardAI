"""
HealthGuard AI — System Monitor (Refactored)
Monitors the target application by polling its health endpoints.
Thread-safe with proper locking and structured logging.
"""

import time
import threading
from typing import Dict, Any, List, Optional

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.monitoring.metrics import (
    TARGET_CPU, TARGET_MEMORY, TARGET_LATENCY, TARGET_ERROR_RATE, TARGET_UP
)

logger = structlog.get_logger(__name__)


class SystemMonitor:
    """
    Monitors the target application by polling its API and metrics endpoints.
    Collects CPU, memory, latency, error rate, and recent logs.
    """

    def __init__(self, target_url: str = None):
        self.target_url = target_url or settings.target_url
        self._cpu_usage = 15.0
        self._memory_usage = 30.0
        self._error_rate = 0.0
        self._response_time = 0.0
        self._logs: List[Dict[str, str]] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start the background monitoring loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        logger.info("system_monitor_started", target_url=self.target_url)

    def stop(self):
        """Stop the background monitoring loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("system_monitor_stopped")

    def set_target_url(self, url: str):
        """Update the monitoring target URL."""
        if not url.startswith("http"):
            url = "https://" + url
        self.target_url = url
        logger.info("target_url_updated", target_url=url)

    def _monitoring_loop(self):
        """Background loop that continuously checks the target system."""
        while self._running:
            if self.target_url:
                self._check_target()
            time.sleep(1)

    def _check_target(self):
        """Perform a health check on the target system."""
        try:
            start = time.time()
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(self.target_url)
            latency = (time.time() - start) * 1000

            with self._lock:
                self._response_time = round(latency, 2)
                TARGET_LATENCY.set(self._response_time)

                if resp.status_code >= 500:
                    self._error_rate = 100.0
                    self._add_log("ERROR", f"HTTP {resp.status_code} Error from {self.target_url}")
                elif resp.status_code == 429:
                    self._error_rate = 100.0
                    self._add_log("WARN", "HTTP 429 Rate Limit Exceeded")
                elif resp.status_code == 503:
                    self._error_rate = 100.0
                    self._add_log("ERROR", "HTTP 503 Network Partition / Service Unavailable")
                else:
                    self._error_rate = 0.0

                TARGET_ERROR_RATE.set(self._error_rate)
                TARGET_UP.set(1)

            # Fetch real system metrics from target
            self._fetch_target_metrics()

        except httpx.TimeoutException:
            with self._lock:
                self._response_time = 10000
                self._error_rate = 0.0
                self._add_log("WARN", "Connection Timed Out (Lag > 10s)")
                TARGET_LATENCY.set(10000)
                TARGET_UP.set(0)

        except Exception as e:
            with self._lock:
                self._error_rate = 100.0
                self._response_time = 0
                self._add_log("ERROR", f"Connection Failed: {str(e)}")
                TARGET_ERROR_RATE.set(100.0)
                TARGET_UP.set(0)

    def _fetch_target_metrics(self):
        """Fetch CPU/Memory metrics from the target's /system/metrics endpoint."""
        try:
            if "api" not in self.target_url:
                return

            base = self.target_url.split("/api")[0]
            metrics_url = f"{base}/system/metrics"

            with httpx.Client(timeout=2.0) as client:
                resp = client.get(metrics_url)
            if resp.status_code == 200:
                data = resp.json()
                with self._lock:
                    self._cpu_usage = data.get("cpu_percent", 0.0)
                    self._memory_usage = data.get("memory_mb", 0.0)
                    TARGET_CPU.set(self._cpu_usage)
                    TARGET_MEMORY.set(self._memory_usage)
        except Exception:
            pass  # Metrics fetch failure is non-critical

    def _add_log(self, level: str, message: str):
        """Add a log entry (called within lock)."""
        if len(self._logs) > 100:
            self._logs.pop(0)
        self._logs.append({
            "timestamp": time.strftime("%H:%M:%S"),
            "level": level,
            "message": message,
        })

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics (thread-safe)."""
        with self._lock:
            return {
                "cpu_percent": round(self._cpu_usage, 2),
                "memory_mb": round(self._memory_usage, 2),
                "error_rate_percent": round(self._error_rate, 2),
                "response_time_ms": round(self._response_time, 2),
                "recent_logs": list(self._logs)[-10:],
            }

    def get_recent_logs(self, limit: int = 5) -> List[Dict[str, str]]:
        """Get recent log entries (thread-safe)."""
        with self._lock:
            return list(self._logs)[-limit:]

    def heal_target(self) -> bool:
        """Trigger the target system's self-healing endpoint."""
        if not self.target_url:
            return False

        try:
            base = self.target_url.split("/api")[0] if "api" in self.target_url else self.target_url.rsplit("/", 1)[0]
            heal_url = f"{base}/chaos/heal"

            logger.info("attempting_remote_heal", url=heal_url)

            with httpx.Client(timeout=5.0) as client:
                client.post(heal_url)

            self._add_log_safe("INFO", f"Sent HEAL command to: {heal_url}")
            return True

        except Exception as e:
            logger.error("remote_heal_failed", error=str(e))
            self._add_log_safe("ERROR", f"Remote Heal Failed: {str(e)}")
            return False

    def _add_log_safe(self, level: str, message: str):
        """Thread-safe log addition."""
        with self._lock:
            self._add_log(level, message)

    def restart_service(self):
        """Maps to heal_target for compatibility."""
        return self.heal_target()

    def clear_cache(self):
        """Maps to heal_target for compatibility."""
        return self.heal_target()

    def inject_failure(self, failure_type: str):
        """Inject a failure into the target system via its chaos endpoint."""
        if not self.target_url:
            return False

        try:
            base = self.target_url.split("/api")[0] if "api" in self.target_url else self.target_url.rsplit("/", 1)[0]

            type_to_endpoint = {
                "MEMORY_LEAK": "/chaos/memory/start",
                "CPU_SPIKE": "/chaos/cpu/start",
                "ERROR_BURST": "/chaos/error/start",
                "LATENCY": "/chaos/latency/start",
                "DB_TIMEOUT": "/chaos/timeout/start",
                "RATE_LIMIT": "/chaos/ratelimit/start",
                "NETWORK_PARTITION": "/chaos/partition/start",
            }

            endpoint = type_to_endpoint.get(failure_type)
            if not endpoint:
                logger.warning("unknown_failure_type", failure_type=failure_type)
                return False

            url = f"{base}{endpoint}"
            logger.info("injecting_failure", type=failure_type, url=url)

            with httpx.Client(timeout=5.0) as client:
                client.post(url)

            return True

        except Exception as e:
            logger.error("failure_injection_failed", error=str(e))
            return False
