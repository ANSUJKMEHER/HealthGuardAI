from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import uvicorn
from main import HealthGuardSystem

app = FastAPI(title="HealthGuard AI Control Plane", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon demo purposes, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global System Instance
system = HealthGuardSystem()
system_thread = None

class FailureRequest(BaseModel):
    type: str  # CPU_SPIKE, MEMORY_LEAK, ERROR_BURST

class MonitorRequest(BaseModel):
    url: str

@app.post("/monitor/url")
def set_monitor_url(request: MonitorRequest):
    system.monitored_system.set_target_url(request.url)
    return {"message": f"Monitoring target set to: {request.url}"}

@app.get("/")
def home():
    return {"status": "HealthGuard AI is online"}

@app.post("/system/start")
def start_system():
    global system_thread
    if system._running:
        return {"message": "System is already running"}
    
    system.start()
    return {"message": "System started successfully"}

@app.post("/system/stop")
def stop_system():
    if not system._running:
        return {"message": "System is not running"}
    
    system.stop()
    return {"message": "System stopped"}

@app.get("/metrics")
def get_metrics():
    if not system._running:
        raise HTTPException(status_code=400, detail="System is not running")
    return system.monitored_system.get_metrics()

@app.post("/inject_failure")
def inject_failure(request: FailureRequest):
    if not system._running:
        raise HTTPException(status_code=400, detail="System is not running")
    
    system.monitored_system.inject_failure(request.type)
    return {"message": f"Injected failure: {request.type}"}

@app.get("/incidents")
def get_incidents():
    # Simple fetch from DB (simulated here for speed, ideally we query the DB object)
    # We'll just return the recent logs from the monitor for now as a proxy or add a method to DB
    # Let's add a quick direct DB query here for the API
    import sqlite3
    conn = sqlite3.connect(system.database.db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT 10")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

@app.get("/export/incidents")
def export_incidents():
    """Export all incidents as JSON"""
    import sqlite3
    import json
    from fastapi.responses import Response
    
    conn = sqlite3.connect(system.database.db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM incidents ORDER BY id DESC")
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    
    json_data = json.dumps(rows, indent=2)
    
    return Response(
        content=json_data,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=healthguard-incidents-{int(time.time())}.json"
        }
    )

@app.get("/export/logs")
def export_logs():
    """Export current system logs as JSON"""
    import json
    import time
    from fastapi.responses import Response
    
    logs = system.monitored_system.get_recent_logs(limit=100)
    metrics = system.monitored_system.get_metrics()
    
    export_data = {
        "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "current_metrics": metrics,
        "recent_logs": logs
    }
    
    json_data = json.dumps(export_data, indent=2)
    
    return Response(
        content=json_data,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=healthguard-logs-{int(time.time())}.json"
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
