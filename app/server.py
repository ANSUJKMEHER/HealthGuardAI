"""
HealthGuard AI — FastAPI Server (v2.0)
Production-grade API with SSE streaming, Prometheus metrics, proper CORS, and health checks.
"""

import json
import time
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import setup_logging
from app.core.engine import HealthGuardEngine
from app.database.session import get_db_dependency, get_db
from app.database.repositories import IncidentRepository
from app.monitoring.metrics import get_prometheus_metrics, FIX_SUCCESS_RATE

# Import TargetApp to bundle it directly
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from TargetApp.main import app as target_app
except ImportError as e:
    target_app = None
    print(f"Failed to import TargetApp: {e}")

import structlog

# ── Setup ────────────────────────────────────────────────────
setup_logging()
logger = structlog.get_logger("server")


# ── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    logger.info("server_starting", version="2.0.0")
    yield
    logger.info("server_shutting_down")
    if engine.is_running:
        engine.stop()


# ── App Definition ─────────────────────────────────────────────
app = FastAPI(
    title="HealthGuard AI - Control Plane",
    description="Backend API for the autonomous healing engine.",
    version="2.0.0",
    lifespan=lifespan,
)

if target_app:
    app.mount("/target", target_app)
    logger.info("mounted_target_app", path="/target")

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instance
engine = HealthGuardEngine()

# SSE event queue for real-time streaming
_sse_events = asyncio.Queue(maxsize=100)


def _on_engine_event(event: dict):
    """Callback from engine — pushes events to SSE queue."""
    try:
        _sse_events.put_nowait(event)
    except asyncio.QueueFull:
        pass  # Drop oldest events if queue is full

engine.add_event_listener(_on_engine_event)


# ── Request Models ───────────────────────────────────────────
class FailureRequest(BaseModel):
    type: str  # MEMORY_LEAK, CPU_SPIKE, ERROR_BURST, LATENCY, DB_TIMEOUT, RATE_LIMIT, NETWORK_PARTITION


class MonitorRequest(BaseModel):
    url: str


# ── Health & Info ────────────────────────────────────────────
@app.get("/")
def root():
    """Root endpoint — API info."""
    return {
        "service": "HealthGuard AI",
        "version": "2.0.0",
        "status": "running" if engine.is_running else "idle",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for deployment platforms (Render, Railway)."""
    return {
        "status": "healthy",
        "uptime": time.time(),
        "engine_running": engine.is_running,
    }


# ── System Control ───────────────────────────────────────────
@app.post("/api/v1/system/start")
def start_system():
    """Start the HealthGuard monitoring engine."""
    if engine.is_running:
        return {"message": "System is already running", "status": "running"}
    engine.start()
    return {"message": "System started successfully", "status": "running"}


@app.post("/api/v1/system/stop")
def stop_system():
    """Stop the HealthGuard monitoring engine."""
    if not engine.is_running:
        return {"message": "System is not running", "status": "stopped"}
    engine.stop()
    return {"message": "System stopped", "status": "stopped"}


@app.get("/api/v1/system/status")
def system_status():
    """Get current system status and stats."""
    with get_db() as db:
        repo = IncidentRepository(db)
        stats = repo.get_stats()

    return {
        "engine_running": engine.is_running,
        "target_url": engine.system_monitor.target_url,
        "llm_provider": settings.llm_provider,
        "stats": stats,
    }


# ── Monitoring Target ───────────────────────────────────────
@app.post("/api/v1/monitor/url")
def update_monitor_url(request: MonitorRequest):
    """Update the target URL that the engine monitors."""
    # Force the use of the natively bundled target app to prevent user errors
    native_url = f"http://127.0.0.1:{os.getenv('PORT', '10000')}/target/api"
    engine.system_monitor.set_target_url(native_url)
    return {"message": "Target URL permanently locked to native bundle", "url": native_url}


# ── Metrics ──────────────────────────────────────────────────
@app.get("/api/v1/metrics")
def get_metrics():
    """Get current target system metrics for the dashboard."""
    if not engine.is_running:
        raise HTTPException(status_code=400, detail="System is not running")
    return engine.system_monitor.get_metrics()


@app.get("/metrics/prometheus")
def prometheus_metrics():
    """Prometheus scrape endpoint — returns metrics in text format."""
    # Update dynamic stats
    with get_db() as db:
        repo = IncidentRepository(db)
        stats = repo.get_stats()
        FIX_SUCCESS_RATE.set(stats["success_rate"])

    return Response(
        content=get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# ── Real-time Streaming (SSE) ───────────────────────────────
@app.get("/api/v1/stream")
async def stream_events():
    """
    Server-Sent Events endpoint for real-time dashboard updates.
    Streams metrics every second + agent events as they happen.
    """
    async def event_generator() -> AsyncGenerator:
        while True:
            # Send current metrics
            if engine.is_running:
                metrics = engine.system_monitor.get_metrics()
                metrics["time"] = time.strftime("%H:%M:%S")
                yield {
                    "event": "metrics",
                    "data": json.dumps(metrics),
                }

            # Drain any agent events from the queue
            while not _sse_events.empty():
                try:
                    event = _sse_events.get_nowait()
                    yield {
                        "event": event.get("type", "update"),
                        "data": json.dumps(event.get("data", {})),
                    }
                except asyncio.QueueEmpty:
                    break

            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())


# ── Chaos Engineering (Failure Injection) ────────────────────
@app.post("/api/v1/inject_failure")
def inject_failure(request: FailureRequest):
    """Inject a failure into the target application for testing."""
    if not engine.is_running:
        raise HTTPException(status_code=400, detail="System is not running. Click START first.")

    success = engine.system_monitor.inject_failure(request.type)
    if success:
        # Emit SSE event so the dashboard shows the injection in the Activity Feed
        _on_engine_event({
            "type": "anomaly_detected",
            "data": {
                "message": f"CHAOS INJECTED: {request.type}",
                "failure_type": request.type,
                "cpu_percent": "—",
                "memory_mb": "—",
            }
        })
        return {"message": f"Injected failure: {request.type}", "success": True, "type": request.type}
    else:
        raise HTTPException(status_code=502, detail=f"Could not reach target app to inject: {request.type}. Check target URL.")


# ── Incidents ────────────────────────────────────────────────
@app.get("/api/v1/incidents")
def get_incidents(db: Session = Depends(get_db_dependency)):
    """Get recent incidents."""
    repo = IncidentRepository(db)
    incidents = repo.get_recent(limit=20)
    return [i.to_dict() for i in incidents]


@app.get("/api/v1/incidents/stats")
def get_incident_stats(db: Session = Depends(get_db_dependency)):
    """Get incident statistics."""
    repo = IncidentRepository(db)
    return repo.get_stats()


@app.get("/api/v1/export/incidents")
def export_incidents(db: Session = Depends(get_db_dependency)):
    """Export all incidents as downloadable JSON."""
    repo = IncidentRepository(db)
    incidents = repo.get_all()
    data = [i.to_dict() for i in incidents]

    return Response(
        content=json.dumps(data, indent=2, default=str),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=healthguard-incidents-{int(time.time())}.json"
        },
    )


# ── Backward Compatibility (old API routes) ──────────────────
# These redirect old endpoints to new v1 API
@app.post("/system/start")
def legacy_start():
    return start_system()

@app.post("/system/stop")
def legacy_stop():
    return stop_system()

@app.get("/metrics")
def legacy_metrics():
    return get_metrics()

@app.post("/inject_failure")
def legacy_inject(request: FailureRequest):
    return inject_failure(request)

@app.get("/incidents")
def legacy_incidents(db: Session = Depends(get_db_dependency)):
    return get_incidents(db)

@app.post("/monitor/url")
def legacy_monitor_url(request: MonitorRequest):
    return set_monitor_url(request)


# ── Entry Point ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.server:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
    )
