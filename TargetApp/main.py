from fastapi import FastAPI, Response, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import time
import asyncio
from typing import List, Optional

app = FastAPI(title="CryptoPulse - High Frequency Ticker")

# Flash Message Context for Admin Panel redirects
flash_message = None

# Market Data State
import random
import threading
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
            # Random Walk Simulation
            for asset in self.prices:
                volatility = 0.0005 # 0.05% change per tick
                change = random.uniform(-volatility, volatility)
                self.prices[asset] *= (1 + change)
            
            self.last_update = time.time()
            time.sleep(0.5) # Update 2x per second

market = MarketEngine()

# Helpers
import psutil
import os
import threading

def get_process_metrics():
    process = psutil.Process(os.getpid())
    return {
        "cpu_percent": process.cpu_percent(interval=None), 
        "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2)
    }

# Global Chaos State
chaos_state = {
    "latency": False,
    "error_500": False,
    "database_timeout": False,
    "rate_limit": False,
    "network_partition": False,
    "memory_leak": False,
    "cpu_spike": False
}

# Leak storage
leak_storage = []

# CPU Stress Thread
cpu_thread = None
cpu_running = False

def cpu_stress_task():
    """Burns CPU by doing intensive math in a loop"""
    while cpu_running:
        # Complex calculation to burn cycles
        [x**2 for x in range(10000)]

# Rate limiting state
request_count = 0
last_reset_time = time.time()

@app.middleware("http")
async def chaos_middleware(request: Request, call_next):
    global request_count, last_reset_time
    
    # Skip chaos for control endpoints and static files
    if (request.url.path.startswith("/admin") or 
        request.url.path.startswith("/chaos") or 
        request.url.path == "/" or
        request.url.path.startswith("/static")):
        return await call_next(request)

    # Rate limiting simulation
    if chaos_state["rate_limit"]:
        current_time = time.time()
        if current_time - last_reset_time > 60:  # Reset every minute
            request_count = 0
            last_reset_time = current_time
        
        request_count += 1
        if request_count > 10:  # Max 10 requests per minute
            return Response(content="Too Many Requests", status_code=429)

    # Network partition (intermittent failures)
    if chaos_state["network_partition"]:
        import random
        if random.random() < 0.3:  # 30% chance of failure
            return Response(content="Service Unavailable - Network Partition", status_code=503)

    # High Latency
    if chaos_state["latency"]:
        await asyncio.sleep(3)

    # Database timeout simulation
    if chaos_state["database_timeout"]:
        await asyncio.sleep(8)  # Long delay

    # 500 Error
    if chaos_state["error_500"]:
        return Response(content="Internal Server Error (Simulated)", status_code=500)

    # Memory Leak Simulation
    if chaos_state["memory_leak"]:
        # Allocate ~10MB per request
        leak_storage.append(" " * 10 * 1024 * 1024)
        
    # CPU Spike is handled by separate thread, but plays nicely here

    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse("static/index.html")

# IMPORTANT: This endpoint is monitored by HealthGuard AI
@app.get("/api")
def health_check():
    """Main API endpoint that HealthGuard monitors. NOW returns Market Data."""
    return {
        "status": "healthy", 
        "service": "CryptoPulse Engine", 
        "market_data": market.prices,
        "timestamp": market.last_update
    }

@app.get("/system/metrics")
def system_metrics():
    """Returns real system metrics (CPU/Memory) for this process"""
    return get_process_metrics()

# Admin/Chaos Controls
@app.get("/admin", response_class=HTMLResponse)
def admin_panel():
    global flash_message
    
    msg_html = ""
    if flash_message:
        msg_html = f"""
        <div style="background: #22c55e; color: black; padding: 15px; margin-bottom: 20px; border-radius: 8px; font-weight: bold; text-align: center; animation: fadeout 4s forwards;">
            ✅ {flash_message}
        </div>
        <style>
            @keyframes fadeout {{
                0% {{ opacity: 1; }}
                70% {{ opacity: 1; }}
                100% {{ opacity: 0; }}
            }}
        </style>
        """
        flash_message = None # Clear after showing

    return f"""
    <html>
        <head>
            <title>Admin - Chaos Controls</title>
            <style>
                body {{ font-family: sans-serif; background: #1a1a1a; color: white; padding: 40px; max-width: 600px; margin: 0 auto; }}
                h1 {{ color: #f59e0b; margin-bottom: 10px; }}
                .subtitle {{ color: #9ca3af; margin-bottom: 30px; }}
                .status {{ margin: 20px 0; padding: 20px; border: 1px solid #333; border-radius: 8px; background: #0a0a0a; }}
                .status-item {{ display: flex; justify-content: space-between; margin: 8px 0; }}
                .status-label {{ color: #9ca3af; }}
                .status-value {{ font-weight: bold; color: {('#22c55e' if not any(chaos_state.values()) else '#ef4444')}; }}
                .btn {{ display: block; width: 100%; padding: 12px; margin: 10px 0; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px; transition: transform 0.2s; }}
                .btn:hover {{ transform: translateX(5px); }}
                .btn-yellow {{ background: #eab308; color: black; }}
                .btn-red {{ background: #ef4444; color: white; }}
                .btn-orange {{ background: #f97316; color: white; }}
                .btn-purple {{ background: #a855f7; color: white; }}
                .btn-blue {{ background: #3b82f6; color: white; }}
                .btn-green {{ background: #22c55e; color: black; font-size: 16px; }}
                .divider {{ border: none; border-top: 1px solid #333; margin: 25px 0; }}
                a {{ color: #22c55e; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>🛠️ Chaos Engineering Panel</h1>
            <p class="subtitle">Inject realistic web service failures</p>
            
            {msg_html}
            
            <div class="status">
                <h3 style="margin-top: 0; color: #fff;">Current Status</h3>
                <div class="status-item">
                    <span class="status-label">High Latency (3s)</span>
                    <span class="status-value">{'ACTIVE' if chaos_state['latency'] else 'Inactive'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">500 Server Crash</span>
                    <span class="status-value">{'ACTIVE' if chaos_state['error_500'] else 'Inactive'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Database Timeout (8s)</span>
                    <span class="status-value">{'ACTIVE' if chaos_state['database_timeout'] else 'Inactive'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Rate Limiting (429)</span>
                    <span class="status-value">{'ACTIVE' if chaos_state['rate_limit'] else 'Inactive'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Network Partition (503)</span>
                    <span class="status-value">{'ACTIVE' if chaos_state['network_partition'] else 'Inactive'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Memory Leak (Leak 10MB/req)</span>
                    <span class="status-value">{'ACTIVE' if chaos_state['memory_leak'] else 'Inactive'}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">CPU Spike (100% Load)</span>
                    <span class="status-value">{'ACTIVE' if chaos_state['cpu_spike'] else 'Inactive'}</span>
                </div>
            </div>

            <form action="/chaos/latency/start" method="post"><button class="btn btn-yellow">🐢 Trigger High Latency</button></form>
            <form action="/chaos/error/start" method="post"><button class="btn btn-red">💥 Trigger Server Crash</button></form>
            <form action="/chaos/timeout/start" method="post"><button class="btn btn-orange">⏱️ Trigger Database Timeout</button></form>
            <form action="/chaos/ratelimit/start" method="post"><button class="btn btn-purple">🚫 Trigger Rate Limiting</button></form>
            <form action="/chaos/partition/start" method="post"><button class="btn btn-blue">📡 Trigger Network Partition</button></form>
            <form action="/chaos/memory/start" method="post"><button class="btn btn-pink" style="background: #ec4899; color: white;">🧠 Trigger Memory Leak</button></form>
            <form action="/chaos/cpu/start" method="post"><button class="btn btn-red" style="background: #ef4444; color: white;">🔥 Trigger CPU Spike</button></form>
            
            <hr class="divider">
            
            <hr class="divider">
            <form action="/chaos/heal" method="post"><button class="btn btn-green">🚑 HEAL ALL ISSUES</button></form>
            
            <p style="margin-top: 30px; text-align: center; opacity: 0.5;"><a href="/">← Back to Todo App</a></p>
        </body>
    </html>
    """

# Chaos Control Endpoints
@app.post("/chaos/latency/start")
def start_latency():
    global flash_message
    chaos_state["latency"] = True
    flash_message = "Latency Injection ACTIVE (3s Delay)"
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/chaos/error/start")
def start_error():
    global flash_message
    chaos_state["error_500"] = True
    flash_message = "Server Crash ACTIVE (HTTP 500)"
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/chaos/timeout/start")
def start_timeout():
    global flash_message
    chaos_state["database_timeout"] = True
    flash_message = "DB Timeout ACTIVE (8s Delay)"
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/chaos/ratelimit/start")
def start_ratelimit():
    global flash_message
    chaos_state["rate_limit"] = True
    flash_message = "Rate Limiting ACTIVE (Max 10 req/min)"
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/chaos/partition/start")
def start_partition():
    global flash_message
    chaos_state["network_partition"] = True
    flash_message = "Network Partition ACTIVE (30% Packet Loss)"
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/chaos/memory/start")
def start_memory_leak():
    global flash_message
    chaos_state["memory_leak"] = True
    flash_message = "Memory Leak STARTED (Consuming RAM...)"
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/chaos/cpu/start")
def start_cpu_spike():
    global flash_message, cpu_running, cpu_thread
    if not cpu_running:
        chaos_state["cpu_spike"] = True
        cpu_running = True
        cpu_thread = threading.Thread(target=cpu_stress_task, daemon=True)
        cpu_thread.start()
    
    flash_message = "CPU Spike STARTED (Burning Core...)"
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/chaos/heal")
def heal_system():
    global leak_storage, cpu_running, flash_message
    chaos_state["latency"] = False
    chaos_state["error_500"] = False
    chaos_state["database_timeout"] = False
    chaos_state["rate_limit"] = False
    chaos_state["network_partition"] = False
    chaos_state["memory_leak"] = False
    chaos_state["cpu_spike"] = False
    
    # Clear memory leak
    leak_storage = [] 
    
    # Stop CPU Spike
    cpu_running = False 
    
    import gc
    gc.collect()
    
    flash_message = "System Healed! All faults cleared."
    return RedirectResponse(url="/admin", status_code=303)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass  # Static directory might not exist yet

if __name__ == "__main__":
    print("Running Task Manager on http://localhost:3000")
    uvicorn.run(app, host="127.0.0.1", port=3000)
