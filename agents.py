import time
from typing import Dict, Any, Optional
from monitored_system import MonitoredSystem
from database import Database
from llm_service import LLMService

class MonitorAgent:
    def __init__(self, system: MonitoredSystem):
        self.system = system

    def observe(self) -> Optional[Dict[str, Any]]:
        metrics = self.system.get_metrics()
        logs = self.system.get_recent_logs()
        
        # Simple detection rules to trigger "Investigation"
        # In a real system, this might use anomaly detection algorithms
        is_cpu_high = metrics['cpu_percent'] > 50 # Lower threshold to catch single-core spike faster
        is_mem_high = metrics['memory_mb'] > 100 # Lower threshold to detect the 10MB/s leak faster
        is_error_high = metrics['error_rate_percent'] > 0 # Any error is bad in this critical system
        is_latency_high = metrics['response_time_ms'] > 2000 # Increased to 2s to allow for network variability
        
        if is_cpu_high or is_mem_high or is_error_high or is_latency_high:
            print(f"[MonitorAgent] ⚠️ ANOMALY DETECTED! CPU: {metrics['cpu_percent']}%, Mem: {metrics['memory_mb']}MB, Err: {metrics['error_rate_percent']}%, Latency: {metrics['response_time_ms']}ms")
            return {
                "metrics": metrics,
                "logs": logs
            }
        
        return None

class DiagnosticianAgent:
    def __init__(self, llm: LLMService, db: Database):
        self.llm = llm
        self.db = db

    def diagnose(self, context: Dict[str, Any], incident_id: int):
        print(f"[DiagnosticianAgent] 🔍 Analyzing root cause...")
        
        # 1. Base Analysis (Simulation)
        diagnosis = self.llm.analyze_situation(context['metrics'], context['logs'])
        
        # 2. Memory / Learning (Check past resolved incidents)
        # In a real system, this would be RAG. Here we simulate looking up "similar" failures.
        # We assume if we diagnosed this before and it was verified, we are more confident.
        # (Simplified: Just check if we have ANY resolved incidents of this predicted root cause)
        
        # Query DB (Simulated fetch for speed)
        past_success = self.db.get_resolved_count_for_failure(diagnosis['root_cause'])
        if past_success > 0:
            diagnosis['thought_process'] += f" [MEMORY] I recall fixing this specific issue {past_success} times successfully in the past."
            diagnosis['confidence'] = min(0.99, diagnosis['confidence'] + 0.05)
            print(f"[DiagnosticianAgent] 🧠 Memory Recall: Found {past_success} past resolutions. Boosted confidence.")

        print(f"[DiagnosticianAgent] 💡 Diagnosis: {diagnosis['root_cause']} (Confidence: {diagnosis['confidence']})")
        self.db.update_diagnosis(incident_id, diagnosis['root_cause'], diagnosis['confidence'])
        
        return diagnosis

class FixerAgent:
    def __init__(self, system: MonitoredSystem, db: Database):
        self.system = system
        self.db = db
        self.SAFE_ACTIONS = ["RESTART_SERVICE", "CLEAR_CACHE", "HEAL_REMOTE_SYSTEM"]

    def execute_fix(self, diagnosis: Dict[str, Any], incident_id: int):
        action = diagnosis.get('recommended_action')
        confidence = diagnosis.get('confidence', 0.0)
        
        if confidence < 0.8:
            print(f"[FixerAgent] 🛑 Confidence too low ({confidence}). Manual intervention required.")
            return False

        if action not in self.SAFE_ACTIONS:
            print(f"[FixerAgent] 🛑 Action '{action}' not in SAFE_LIST. Aborting.")
            return False

        print(f"[FixerAgent] 🛠️ Executing Autonomous Fix: {action}...")
        self.db.log_action(incident_id, action)
        
        if action == "RESTART_SERVICE":
            self.system.restart_service()
            return True
        elif action == "CLEAR_CACHE":
            self.system.clear_cache()
            return True
        elif action == "HEAL_REMOTE_SYSTEM":
            return self.system.heal_target()
        
        return False

class ReporterAgent:
    def __init__(self, llm: LLMService, db: Database):
        self.llm = llm
        self.db = db

    def verify_and_report(self, system: MonitoredSystem, incident_id: int, diagnosis_data: Dict[str, Any], action: str):
        print(f"[ReporterAgent] 🧪 Verifying recovery...")
        time.sleep(3) # Wait for system to stabilize
        
        metrics = system.get_metrics()
        # Verification Check
        is_recovered = metrics['cpu_percent'] < 50 and metrics['memory_mb'] < 100
        
        self.db.verify_recovery(incident_id, is_recovered)
        
        if is_recovered:
            print(f"[ReporterAgent] ✅ System Recovered! Generating Incident Report...")
            
            incident_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "failure_type": diagnosis_data['root_cause'], # Using root cause as title
                "diagnosis": diagnosis_data,
                "action_taken": action
            }
            
            report = self.llm.generate_report(incident_data)
            print("\n" + "="*40)
            print(report)
            print("="*40 + "\n")
            return report
        else:
            print(f"[ReporterAgent] ❌ Verification Failed. System still unstable.")
            return None
