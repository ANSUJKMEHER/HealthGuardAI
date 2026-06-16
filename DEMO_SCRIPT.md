# 🎤 HealthGuard AI - Live Demo Script

**Goal:** Convince the judges/audience that HealthGuard AI is a reliable, autonomous SRE teammate that saves money and sleep.
**Duration:** ~3 Minutes

---

## ⚙️ 1. Pre-Demo Setup (Do this 5 minutes before)
1.  **Terminal 1 (Backend Control Plane):**
    ```powershell
    cd HealthGuardAI
    python server.py
    ```
2.  **Terminal 2 (Target Application):**
    ```powershell
    cd TargetApp
    python main.py
    ```
3.  **Terminal 3 (Frontend Dashboard):**
    ```powershell
    cd HealthGuardAI/frontend
    npm run dev
    ```
4.  **Browser:** Open `http://localhost:5173`.
    *   *Tip: Press F11 for Full Screen mode to look professional.*
    *   *Tip: Clear the "Incident History" (Refresh the page).*

---

## 🎬 2. The Script (Step-by-Step)

### Phase 1: The Hook (0:00 - 0:30)
**Action:** Show the **Green** Dashboard.
**Say:**
> "Every minute of downtime costs companies thousands of dollars. Engineers are waking up at 3 AM to fix server crashes manually. But what if your infrastructure could heal itself?
> Introducing **HealthGuard AI**: An autonomous multi-agent system that detects, diagnoses, and fixes critical failures without human intervention."

### Phase 2: Normal Operation (0:30 - 0:45)
**Action:** Click **"START SYSTEM"** on the dashboard.
**Say:**
> "Right now, HealthGuard is monitoring our target application. You can see the real-time telemetry here using `psutil` metrics. The **Monitor Agent** is checking CPU, Memory, and Error rates every second. Everything is stable."

### Phase 3: The "Disaster" (0:45 - 1:15)
**Action:** Click the **"Inject Failure"** dropdown (or button) and select **"MEMORY LEAK"**.
**Say:**
> "Now, let's simulate a disaster. I'm injecting a **Critical Memory Leak** into the live application."

**Action:** Point to the **Yellow Memory Line** on the chart.
**Say:**
> "Watch the yellow line. Memory is spiking out of control. In a normal world, the server would crash, and customers would face downtime."

### Phase 4: Autonomous Healing (1:15 - 2:00)
**Action:** Point to the **Logs/Terminal** window in the dashboard.
**Say:**
> "But watch the logs. The **Monitor Agent** just flagged the anomaly.
> Now, the **Diagnostician Agent** (powered by LLM logic) is analyzing the root cause... It sees the 'OutOfMemory' pattern."
>
> *Wait for the line to drop back down.*
>
> "Boom! The **Fixer Agent** just intervened. It decided the safest action was to **Restart the Service** to clear the heap. The memory has dropped back to stable levels. The system healed itself in seconds, not hours."

### Phase 5: The Post-Mortem (2:00 - 2:30)
**Action:** Click **"Export Incidents"** (Blue Button). Open the downloaded JSON file.
**Say:**
> "Finally, the **Reporter Agent** verifies the fix and logs everything. I can download the full incident report here, showing exactly what went wrong and how the AI fixed it. This provides full auditability for the engineering team."

### Phase 6: Closing (2:30 - 3:00)
**Say:**
> "HealthGuard AI turns reactive debugging into proactive immunity. Thank you."

---

## ⚡ Cheat Sheet: "What if it goes wrong?"
-   **If metrics don't load:** Refresh the page. Ensure `server.py` and `main.py` are both running.
-   **If the AI doesn't react:** Click "Inject Failure" again. Sometimes the "Safe Mode" prevents duplicate triggers too fast.
-   **Talking Point for Judges:** "We implemented a Safety Layer (Human-in-the-Loop) for low-confidence decisions, but for clear patterns like this, it acts autonomously."
