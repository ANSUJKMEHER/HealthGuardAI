import time
import threading
from monitored_system import MonitoredSystem
from database import Database
from llm_service import LLMService
from agents import MonitorAgent, DiagnosticianAgent, FixerAgent, ReporterAgent

class HealthGuardSystem:
    def __init__(self):
        self.monitored_system = MonitoredSystem()
        self.database = Database()
        self.llm_service = LLMService()
        
        # Initialize Agents
        self.monitor = MonitorAgent(self.monitored_system)
        self.diagnostician = DiagnosticianAgent(self.llm_service, self.database)
        self.fixer = FixerAgent(self.monitored_system, self.database)
        self.reporter = ReporterAgent(self.llm_service, self.database)
        
        self._running = False
        self._thread = None

    def start(self):
        print(f"[HealthGuard] 🟢 System Started. Monitoring active on: {self.monitored_system.target_url}")
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        print("[HealthGuard] 🔴 System Stopping...")
        self._running = False
        self.monitored_system.stop()
        if self._thread:
            self._thread.join()

    def _run_loop(self):
        while self._running:
            try:
                # 1. MONITOR SECTION
                anomaly_context = self.monitor.observe()
                
                if anomaly_context:
                    # Log incident start
                    incident_id = self.database.log_incident("ANOMALY_DETECTED")
                    
                    # 2. DIAGNOSIS SECTION
                    diagnosis = self.diagnostician.diagnose(anomaly_context, incident_id)
                    
                    # 3. FIX SECTION
                    fix_executed = self.fixer.execute_fix(diagnosis, incident_id)
                    
                    if fix_executed:
                        # 4. REPORT SECTION
                        self.reporter.verify_and_report(
                            self.monitored_system, 
                            incident_id, 
                            diagnosis, 
                            diagnosis['recommended_action']
                        )
                        
                        # Wait a bit after a fix loop to let system clear up
                        time.sleep(5)
            
            except Exception as e:
                print(f"[HealthGuard] 💥 Critical Loop Error: {e}")
            
            time.sleep(2) # Poll interval
