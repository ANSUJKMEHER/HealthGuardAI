import sqlite3
import json
import time

class Database:
    def __init__(self, db_path="healthguard.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Incidents table
        c.execute('''CREATE TABLE IF NOT EXISTS incidents
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      failure_type TEXT,
                      status TEXT,
                      diagnosis TEXT,
                      action_taken TEXT,
                      recovery_verified BOOLEAN)''')
        
        conn.commit()
        conn.close()

    def get_resolved_count_for_failure(self, failure_type: str) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM incidents 
            WHERE failure_type = ? AND status = 'RESOLVED'
        """, (failure_type,))
        try:
           count = c.fetchone()[0]
        except:
           count = 0
        conn.close()
        return count

    def log_incident(self, failure_type: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO incidents (timestamp, failure_type, status, recovery_verified) VALUES (?, ?, ?, ?)",
                  (time.strftime("%Y-%m-%d %H:%M:%S"), failure_type, "DETECTED", False))
        incident_id = c.lastrowid
        conn.commit()
        conn.close()
        return incident_id

    def update_diagnosis(self, incident_id: int, diagnosis: str, confidence: float):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        diag_json = json.dumps({"root_cause": diagnosis, "confidence": confidence})
        # UPDATE: Also update failure_type to be specific (e.g. "Database Timeout") instead of generic "ANOMALY_DETECTED"
        c.execute("UPDATE incidents SET diagnosis = ?, status = 'DIAGNOSED', failure_type = ? WHERE id = ?", (diag_json, diagnosis, incident_id))
        conn.commit()
        conn.close()

    def log_action(self, incident_id: int, action: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE incidents SET action_taken = ?, status = 'FIX_ATTEMPTED' WHERE id = ?", (action, incident_id))
        conn.commit()
        conn.close()

    def verify_recovery(self, incident_id: int, resolved: bool):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        status = "RESOLVED" if resolved else "FAILED"
        c.execute("UPDATE incidents SET recovery_verified = ?, status = ? WHERE id = ?", (resolved, status, incident_id))
        conn.commit()
        conn.close()
