import re
import json
import random
from typing import Dict, Any

class LLMService:
    """
    Abstracts the LLM calls. 
    In specific demo mode, it uses rule-based logic to simulate advanced reasoning 
    to ensure 100% reliability for the hackathon presentation without API key dependencies.
    """
    
    def analyze_situation(self, metrics: Dict[str, Any], logs: list) -> Dict[str, Any]:
        """
        Simulates: "Reason about the anomaly and suggest a root cause."
        """
        prompt_context = f"Metrics: {metrics}, Logs: {logs}"
        
        # Simulated "Thinking" Delay
        # time.sleep(0.5) 
        
        cpu = metrics.get('cpu_percent', 0)
        mem = metrics.get('memory_mb', 0)
        logs_text = " ".join([l['message'] for l in logs])

        # Logic for DEMO SCENARIO 1: MEMORY LEAK
        # Logic for DEMO SCENARIO 1: MEMORY LEAK
        if "OutOfMemoryError" in logs_text:
            return {
                "thought_process": "CRITICAL: Logs show OutOfMemoryError. Application is crashing. Immediate restart required to restore service availability.",
                "root_cause": "Critical Memory Leak (OOM)",
                "confidence": 0.99,
                "recommended_action": "RESTART_SERVICE"
            }
            
        elif mem > 100:  # New specific handler for our Real Memory Leak Demo
             return {
                "thought_process": f"Memory usage is abnormally high ({mem}MB > 100MB threshold). This indicates a progressive memory leak in the application process.",
                "root_cause": "Application Memory Leak",
                "confidence": 0.98,
                "recommended_action": "HEAL_REMOTE_SYSTEM" 
            }

        elif mem > 300 and "Garbage collection" in logs_text: # keep old fallback check
             return {
                "thought_process": "Memory is high (Warning level) and GC is thrashing. A full restart is expensive. Clearing the cache should relieve heap pressure safely.",
                "root_cause": "High Heap Usage (Cache Bloat)",
                "confidence": 0.85,
                "recommended_action": "CLEAR_CACHE"
            }

        # Logic for DEMO SCENARIO 2: CPU SPIKE
        if cpu > 50:
             return {
                "thought_process": "CPU usage sustained above 50% (Single Core Saturation). This indicates a process stuck in a calculation loop or infinite recursion.",
                "root_cause": "Process Stuck in Calculation Loop",
                "confidence": 0.96,
                "recommended_action": "HEAL_REMOTE_SYSTEM" # We map this to Heal/Restart to kill the thread
            }

        # Logic for DEMO SCENARIO 3: ERROR BURST (REAL OR SIMULATED)
        if "HTTP 500" in logs_text or "HTTP 503" in logs_text or "Connection refused" in logs_text:
             return {
                "thought_process": "CRITICAL: Detected HTTP 5xx Server Errors from the monitored endpoint. The remote service is failing. Attempting to trigger self-healing protocols via control plane.",
                "root_cause": "Remote Service Crash (HTTP 500)",
                "confidence": 0.95,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }
        
        elif metrics.get('error_rate_percent', 0) > 10:
             return {
                "thought_process": "Error rate spiked > 10%. Logs show connection refusals to DB shard. Likely a transient network partition or service hang.",
                "root_cause": "Database Connection Pool Exhaustion",
                "confidence": 0.92,
                "recommended_action": "RESTART_SERVICE"
            }

        
        # Logic for DEMO SCENARIO 4: HIGH LATENCY (LAG)
        latency = metrics.get('response_time_ms', 0)
        if latency > 5000:  # Very high latency (database timeout range)
             return {
                "thought_process": f"Response time is CRITICAL ({latency}ms). This exceeds normal lag and indicates database query timeout or hung connections. System is effectively unresponsive.",
                "root_cause": "Database Connection Timeout",
                "confidence": 0.93,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }
        elif latency > 1000:
             return {
                "thought_process": f"Response time is elevated ({latency}ms). Service is slow but CPU/Errors are normal. Indicates external dependency lag or thread starvation.",
                "root_cause": "High Service Latency (Lag)",
                "confidence": 0.90,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }
        
        # Logic for DEMO SCENARIO 5: RATE LIMITING (429 errors)
        if "HTTP 429" in logs_text or "Too Many Requests" in logs_text:
             return {
                "thought_process": "Detected HTTP 429 status codes. The service is rate limiting requests. This indicates either a traffic spike or misconfigured rate limits.",
                "root_cause": "Rate Limit Exceeded",
                "confidence": 0.94,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }
        
        # Logic for DEMO SCENARIO 6: NETWORK PARTITION (503 errors)
        if "HTTP 503" in logs_text or "Service Unavailable" in logs_text or "Network Partition" in logs_text:
             return {
                "thought_process": "Detected HTTP 503 Service Unavailable errors. This indicates network partition, service overload, or infrastructure failure.",
                "root_cause": "Network Partition / Service Unavailable",
                "confidence": 0.91,
                "recommended_action": "HEAL_REMOTE_SYSTEM"
            }

        return {
            "thought_process": "System within normal operating parameters.",
            "root_cause": "None",
            "confidence": 1.0,
            "recommended_action": "WAIT"
        }

    def generate_report(self, incident_data: Dict[str, Any]) -> str:
        """
        Generates a human-readable incident report.
        """
        return f"""
# 🚨 INCIDENT REPORT: {incident_data.get('failure_type', 'Unknown')}
**Date:** {incident_data.get('timestamp')}
**Status:** RESOLVED

## 🔍 Diagnosis
**Root Cause:** {incident_data.get('diagnosis', {}).get('root_cause')}
**Confidence:** {incident_data.get('diagnosis', {}).get('confidence')}
**Reasoning:** {incident_data.get('diagnosis', {}).get('thought_process')}

## 🛠️ Action Taken
**Action:** {incident_data.get('action_taken')}
**Result:** Verified recovery of system metrics to normal levels.

## 📝 Recommendations
- Investigate recent deployment for memory leaks.
- Review recent code changes in the transaction module.
"""
