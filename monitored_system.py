import time
import threading
import requests
from typing import Dict, Any, List

class MonitoredSystem:
    def __init__(self):
        self._cpu_usage = 15.0
        self._memory_usage = 30.0
        self._error_rate = 0.0
        self._response_time = 0
        self._logs: List[Dict[str, str]] = []
        self._lock = threading.Lock()
        
        # Real Monitoring Target - Default to 127.0.0.1 to avoid localhost DNS lag
        self.target_url = "http://127.0.0.1:3000/api"
        self._running = True
        
        # Start monitoring thread
        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()

    def _monitoring_loop(self):
        while self._running:
            if self.target_url:
                # Perform network check OUTSIDE the lock to prevent blocking API calls
                self._check_real_website()
            time.sleep(1) # Poll every second

    def _check_real_website(self):
        try:
            start = time.time()
            resp = requests.get(self.target_url, timeout=10)
            latency = (time.time() - start) * 1000
            
            # Update metrics safely inside lock
            with self._lock:
                self._response_time = round(latency, 2)
                
                if resp.status_code >= 500:
                     self._error_rate = 100.0
                     self._generate_log("ERROR", f"HTTP {resp.status_code} Error from {self.target_url}")
                elif resp.status_code == 429:
                     self._error_rate = 100.0
                     self._generate_log("WARN", f"HTTP 429 Rate Limit Exceeded")
                elif resp.status_code == 503:
                     self._error_rate = 100.0
                     self._generate_log("ERROR", f"HTTP 503 Network Partition / Service Unavailable")
                else:
                     self._error_rate = 0.0

            # Fetch Real System Metrics (Separate call to avoid blocking main check if this fails)
            try:
                # Construct metrics URL (replace /api with /system/metrics)
                if "api" in self.target_url:
                    base = self.target_url.split("/api")[0]
                    metrics_url = f"{base}/system/metrics"
                    
                    metric_resp = requests.get(metrics_url, timeout=2)
                    if metric_resp.status_code == 200:
                        data = metric_resp.json()
                        with self._lock:
                            self._cpu_usage = data.get("cpu_percent", 0.0)
                            self._memory_usage = data.get("memory_mb", 0.0)
            except Exception:
                pass # Fail silently for metrics, keep main monitoring alive
            
        except requests.exceptions.Timeout:
            with self._lock:
                self._response_time = 10000 
                self._error_rate = 0.0 
                self._generate_log("WARN", f"Connection Timed Out (Lag > 10s)")
            
        except Exception as e:
            with self._lock:
                self._error_rate = 100.0
                self._response_time = 0
                self._generate_log("ERROR", f"Connection Failed: {str(e)}")

    def _generate_log(self, level: str, message: str):
        # Keep logs limited
        if len(self._logs) > 100:
            self._logs.pop(0)
        
        self._logs.append({
            "timestamp": time.strftime("%H:%M:%S"),
            "level": level,
            "message": message
        })

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            # CPU/Memory are now fetched from the TargetApp via /system/metrics
            return {
                "cpu_percent": self._cpu_usage, 
                "memory_mb": self._memory_usage,
                "error_rate_percent": round(self._error_rate, 2),
                "response_time_ms": round(self._response_time, 2),
                "active_failure": None, # Removed active_failure state tracking since it doesn't apply to real blackbox monitoring
                "recent_logs": list(self._logs)[-10:]
            }

    def get_recent_logs(self, limit: int = 5) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._logs)[-limit:]

    # Removed inject_failure() - No longer needed, failures are real from TargetApp
    # Removed restart_service() - Cannot restart remote service locally
    # Removed clear_cache() - Cannot clear remote cache locally

    def heal_target(self):
        """
        Attempts to find a /chaos/heal endpoint on the monitoring target and Trigger it.
        This closes the loop for the demo apps.
        """
        if not self.target_url: 
            return False
            
        try:
            # Assume target_url is like http://localhost:3000/api -> http://localhost:3000/chaos/heal
            base = self.target_url.rsplit('/', 1)[0] # Strip last segment
            heal_url = f"{base}/chaos/heal"
            
            # Try root base as fallback
            if "api" in self.target_url:
                 base = self.target_url.split("/api")[0]
                 heal_url = f"{base}/chaos/heal"

            print(f"\n[SYSTEM] >>> ATTEMPTING REMOTE HEAL: {heal_url} <<<\n")
            requests.post(heal_url, timeout=2)
            self._generate_log("INFO", f"Sent HEAL command to remote target: {heal_url}")
            return True
        except Exception as e:
            # If the heal command fails (e.g. network partition is too strong), log it
            self._generate_log("ERROR", f"Remote Heal Failed: {str(e)}")
            return False

    def restart_service(self):
        # Kept for compatibility with agents.py calling restart_service
        # For the demo, "Restart Service" action maps to "Heal Target"
        return self.heal_target()

    def clear_cache(self):
        # Kept for compatibility with agents.py
        # For the demo, "Clear Cache" action maps to "Heal Target"
        return self.heal_target()
        
    def stop(self):
        self._running = False
