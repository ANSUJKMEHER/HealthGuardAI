"""
CryptoPulse — High-Frequency Trading Engine (Target Application)
This is the application that HealthGuard AI monitors and auto-heals.
It includes chaos engineering endpoints for failure injection.
"""

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import time
import asyncio
import random
import threading
import psutil
import os
import gc

app = FastAPI(title="CryptoPulse - High Frequency Trading Engine")

# ── CORS (allow HealthGuard API to call chaos endpoints) ────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Market Engine ───────────────────────────────────────────
class MarketEngine:
    def __init__(self):
        self.prices = {
            "BTC": 96500.00,
            "ETH": 2800.00,
            "GOLD": 2150.00,
            "SILVER": 24.50
        }
        self.last_update = time.time()
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_loop(self):
        while self._running:
            for asset in self.prices:
                volatility = 0.0005
                change = random.uniform(-volatility, volatility)
                self.prices[asset] *= (1 + change)
            self.last_update = time.time()
            time.sleep(0.5)

market = MarketEngine()

# ── Process Metrics ─────────────────────────────────────────
_process = psutil.Process(os.getpid())

def get_process_metrics():
    return {
        "cpu_percent": _process.cpu_percent(interval=None),
        "memory_mb": round(_process.memory_info().rss / 1024 / 1024, 2)
    }

# ── Chaos State ─────────────────────────────────────────────
chaos_state = {
    "latency": False,
    "error_500": False,
    "database_timeout": False,
    "rate_limit": False,
    "network_partition": False,
    "memory_leak": False,
    "cpu_spike": False
}

leak_storage = []
cpu_thread = None
cpu_running = False

def cpu_stress_task():
    """Burns CPU by doing intensive math in a loop"""
    while cpu_running:
        [x**2 for x in range(10000)]

# Rate limiting state
request_count = 0
last_reset_time = time.time()

# ── Chaos Middleware ────────────────────────────────────────
@app.middleware("http")
async def chaos_middleware(request: Request, call_next):
    global request_count, last_reset_time

    # Skip chaos for control/admin/chaos endpoints and static files
    path = request.url.path
    if (path.startswith("/admin") or
        path.startswith("/chaos") or
        path == "/" or
        path == "/system/metrics" or
        path.startswith("/static")):
        return await call_next(request)

    # Rate limiting simulation
    if chaos_state["rate_limit"]:
        current_time = time.time()
        if current_time - last_reset_time > 60:
            request_count = 0
            last_reset_time = current_time
        request_count += 1
        if request_count > 10:
            return Response(content="Too Many Requests", status_code=429)

    # Network partition (intermittent failures)
    if chaos_state["network_partition"]:
        if random.random() < 0.3:
            return Response(content="Service Unavailable - Network Partition", status_code=503)

    # High Latency
    if chaos_state["latency"]:
        await asyncio.sleep(3)

    # Database timeout simulation
    if chaos_state["database_timeout"]:
        await asyncio.sleep(8)

    # 500 Error
    if chaos_state["error_500"]:
        return Response(content="Internal Server Error (Simulated)", status_code=500)

    # Memory Leak Simulation
    if chaos_state["memory_leak"]:
        leak_storage.append(" " * 10 * 1024 * 1024)

    return await call_next(request)


# ── Main Endpoints ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/", response_class=HTMLResponse)
def home():
    try:
        return FileResponse(os.path.join(BASE_DIR, "static/index.html"))
    except Exception:
        return HTMLResponse("<h1>CryptoPulse Engine Running</h1><p><a href='/api'>API</a> | <a href='/admin'>Admin</a></p>")


@app.get("/api")
def health_check():
    """Main API endpoint that HealthGuard monitors."""
    return {
        "status": "healthy",
        "service": "CryptoPulse Engine",
        "market_data": market.prices,
        "timestamp": market.last_update,
        "chaos_active": [k for k, v in chaos_state.items() if v],
    }


@app.get("/system/metrics")
def system_metrics():
    """Returns real system metrics (CPU/Memory) for this process."""
    return get_process_metrics()


# ── Chaos Status ────────────────────────────────────────────
@app.get("/chaos/status")
def chaos_status():
    """Returns current chaos state as JSON."""
    return {
        "chaos_state": chaos_state,
        "any_active": any(chaos_state.values()),
        "active_faults": [k for k, v in chaos_state.items() if v],
        "leaked_mb": len(leak_storage) * 10,
    }


# ── Chaos Control Endpoints (return JSON) ───────────────────
@app.post("/chaos/latency/start")
def start_latency():
    chaos_state["latency"] = True
    return JSONResponse({"status": "active", "type": "latency", "message": "Latency Injection ACTIVE (3s Delay)"})


@app.post("/chaos/error/start")
def start_error():
    chaos_state["error_500"] = True
    return JSONResponse({"status": "active", "type": "error_500", "message": "Server Crash ACTIVE (HTTP 500)"})


@app.post("/chaos/timeout/start")
def start_timeout():
    chaos_state["database_timeout"] = True
    return JSONResponse({"status": "active", "type": "database_timeout", "message": "DB Timeout ACTIVE (8s Delay)"})


@app.post("/chaos/ratelimit/start")
def start_ratelimit():
    chaos_state["rate_limit"] = True
    return JSONResponse({"status": "active", "type": "rate_limit", "message": "Rate Limiting ACTIVE (Max 10 req/min)"})


@app.post("/chaos/partition/start")
def start_partition():
    chaos_state["network_partition"] = True
    return JSONResponse({"status": "active", "type": "network_partition", "message": "Network Partition ACTIVE (30% Packet Loss)"})


@app.post("/chaos/memory/start")
def start_memory_leak():
    chaos_state["memory_leak"] = True
    return JSONResponse({"status": "active", "type": "memory_leak", "message": "Memory Leak STARTED (Consuming RAM...)"})


@app.post("/chaos/cpu/start")
def start_cpu_spike():
    global cpu_running, cpu_thread
    if not cpu_running:
        chaos_state["cpu_spike"] = True
        cpu_running = True
        cpu_thread = threading.Thread(target=cpu_stress_task, daemon=True)
        cpu_thread.start()
    return JSONResponse({"status": "active", "type": "cpu_spike", "message": "CPU Spike STARTED (Burning Core...)"})


@app.post("/chaos/heal")
def heal_system():
    global leak_storage, cpu_running
    chaos_state["latency"] = False
    chaos_state["error_500"] = False
    chaos_state["database_timeout"] = False
    chaos_state["rate_limit"] = False
    chaos_state["network_partition"] = False
    chaos_state["memory_leak"] = False
    chaos_state["cpu_spike"] = False

    leak_storage = []
    cpu_running = False
    gc.collect()

    return JSONResponse({"status": "healed", "message": "System Healed! All faults cleared."})


# ── Admin Panel ─────────────────────────────────────────────
@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    active_color = '#ef4444'
    inactive_color = '#22c55e'
    overall_color = inactive_color if not any(chaos_state.values()) else active_color

    def status_badge(key, label):
        is_active = chaos_state[key]
        color = active_color if is_active else '#4ade80'
        text = 'ACTIVE' if is_active else 'Inactive'
        return f'''
            <div class="status-item">
                <span class="status-label">{label}</span>
                <span style="color: {color}; font-weight: bold;">{text}</span>
            </div>'''

    return f"""
    <html>
        <head>
            <title>CryptoPulse Admin - Chaos Controls</title>
            <style>
                body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; max-width: 600px; margin: 0 auto; }}
                h1 {{ color: #f59e0b; margin-bottom: 10px; }}
                .subtitle {{ color: #94a3b8; margin-bottom: 30px; }}
                .status {{ margin: 20px 0; padding: 20px; border: 1px solid #334155; border-radius: 12px; background: #1e293b; }}
                .status-item {{ display: flex; justify-content: space-between; margin: 8px 0; padding: 4px 0; }}
                .status-label {{ color: #94a3b8; }}
                .btn {{ display: block; width: 100%; padding: 14px; margin: 8px 0; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; font-size: 14px; transition: all 0.2s; letter-spacing: 0.5px; }}
                .btn:hover {{ transform: translateX(5px); filter: brightness(1.1); }}
                .btn-yellow {{ background: #eab308; color: #1a1a1a; }}
                .btn-red {{ background: #ef4444; color: white; }}
                .btn-orange {{ background: #f97316; color: white; }}
                .btn-purple {{ background: #a855f7; color: white; }}
                .btn-blue {{ background: #3b82f6; color: white; }}
                .btn-pink {{ background: #ec4899; color: white; }}
                .btn-green {{ background: #22c55e; color: #1a1a1a; font-size: 16px; margin-top: 20px; }}
                hr {{ border: none; border-top: 1px solid #334155; margin: 25px 0; }}
                a {{ color: #38bdf8; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                #feedback {{ text-align: center; padding: 12px; margin: 10px 0; border-radius: 8px; display: none; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>⚡ Chaos Engineering Panel</h1>
            <p class="subtitle">Inject realistic web service failures</p>

            <div id="feedback"></div>

            <div class="status" id="status-panel">
                <h3 style="margin-top: 0; color: #fff;">Current Status</h3>
                {status_badge("latency", "High Latency (3s)")}
                {status_badge("error_500", "500 Server Crash")}
                {status_badge("database_timeout", "Database Timeout (8s)")}
                {status_badge("rate_limit", "Rate Limiting (429)")}
                {status_badge("network_partition", "Network Partition (503)")}
                {status_badge("memory_leak", "Memory Leak (10MB/req)")}
                {status_badge("cpu_spike", "CPU Spike (100% Load)")}
            </div>

            <button class="btn btn-yellow" onclick="inject('/chaos/latency/start')">🐢 Trigger High Latency</button>
            <button class="btn btn-red" onclick="inject('/chaos/error/start')">💥 Trigger Server Crash</button>
            <button class="btn btn-orange" onclick="inject('/chaos/timeout/start')">⏱️ Trigger Database Timeout</button>
            <button class="btn btn-purple" onclick="inject('/chaos/ratelimit/start')">🚫 Trigger Rate Limiting</button>
            <button class="btn btn-blue" onclick="inject('/chaos/partition/start')">📡 Trigger Network Partition</button>
            <button class="btn btn-pink" onclick="inject('/chaos/memory/start')">🧠 Trigger Memory Leak</button>
            <button class="btn btn-red" onclick="inject('/chaos/cpu/start')">🔥 Trigger CPU Spike</button>

            <hr>
            <button class="btn btn-green" onclick="inject('/chaos/heal')">🚑 HEAL ALL ISSUES</button>

            <p style="margin-top: 30px; text-align: center; opacity: 0.5;"><a href="/">← Back to CryptoPulse</a></p>

            <script>
                async function inject(endpoint) {{
                    const fb = document.getElementById('feedback');
                    try {{
                        const resp = await fetch(endpoint, {{ method: 'POST' }});
                        const data = await resp.json();
                        fb.style.display = 'block';
                        fb.style.background = '#22c55e';
                        fb.style.color = '#000';
                        fb.textContent = '✅ ' + data.message;
                        setTimeout(() => location.reload(), 1500);
                    }} catch (err) {{
                        fb.style.display = 'block';
                        fb.style.background = '#ef4444';
                        fb.style.color = '#fff';
                        fb.textContent = '❌ Failed: ' + err.message;
                    }}
                }}
            </script>
        </body>
    </html>
    """


# ── Static Files ────────────────────────────────────────────
from fastapi.staticfiles import StaticFiles
try:
    app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
except Exception:
    pass

if __name__ == "__main__":
    print("Running CryptoPulse on http://localhost:3000")
    uvicorn.run(app, host="127.0.0.1", port=3000)
