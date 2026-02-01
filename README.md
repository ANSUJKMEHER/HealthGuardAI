# HealthGuard AI 🛡️

**An Autonomous Infrastructure Sentinel for Mission-Critical Systems.**

HealthGuard AI is a multi-agent system that continuously monitors signals, detects anomalies, diagnoses root causes using LLM reasoning, and performs safe autonomous fixes.

![Dashboard](https://via.placeholder.com/800x400?text=HealthGuard+AI+Dashboard)

## 🌟 Features
- **4-Agent Architecture**: Monitor, Diagnostician, Fixer, Reporter.
- **Autonomous Healing**: Detects and fixes CPU spikes and Memory leaks without human input.
- **Real-time Dashboard**: React + Vite + Tailwind CSS interface.
- **Simulated Environment**: Realistic metrics generator for consistent demos.

## 🛠️ Tech Stack
- **Languages**: Python 3.10+, JavaScript (React)
- **Backend**: FastAPI
- **Frontend**: Vite, React, Recharts, Tailwind CSS
- **Database**: SQLite
- **AI Logic**: Deterministic Rule-Based Stub (Swappable for OpenAI/Claude)

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+

### Installation
1. Clone the repo.
2. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn
   ```
3. Install Frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Running the Demo
You can run the system in two modes:

#### Option A: Terminal Demo (No UI)
Run the self-contained script to see the agents in the console:
```bash
python demo.py
```

#### Option B: Full Dashboard (Recommended)
1. **Start the Backend**:
   ```bash
   python server.py
   ```
2. **Start the Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
3. **Open Browser**: Go to `http://localhost:5173`

## 🧪 How to Demo
1. Click **START SYSTEM** in the dashboard.
2. Watch the stable metrics (Green).
3. Click **MEMORY LEAK** in the "Failure Injection" panel.
4. **Observe**:
   - Memory line (Yellow) spikes.
   - Logs show "Detection".
   - Agents diagnose the issue.
   - Agents **RESTART** the service automatically.
   - Metrics stabilize.

## 📂 Project Structure
- `agents.py`: core logic for Monitor, Diagnostician, Fixer, Reporter.
- `monitored_system.py`: Simulation engine for metrics.
- `server.py`: FastAPI control plane.
- `frontend/`: React dashboard code.

---
*Built for Hackathons. Deterministic. Autonomous.*
