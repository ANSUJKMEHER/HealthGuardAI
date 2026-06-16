# HealthGuard AI - Prompt Engineering & Agent Documentation

This document acts as the official record of the Large Language Model (LLM) strategies, prompt templates, and system instructions used in the HealthGuard AI autonomous infrastructure protection system.

## 📂 Project Overview
**Project**: HealthGuard AI
**Domain**: Artificial Intelligence (AIOps)
**Goal**: Create a self-healing infrastructure system that uses agentic reasoning to detect, diagnose, and fix failures without human intervention.

---

## 🏗️ 1. Master Prompt Templates
The following templates represent the "Production" prompts used by the system during runtime.

### 🔍 A. Diagnostician Agent Logic
**Purpose**: To reason about raw signals and determine if a system intervention is safe and necessary.

**System Prompt:**
```text
You are the Senior Site Reliability Engineer (SRE) Agent for HealthGuard AI.
Your specific role is **Root Cause Analysis**.
You are connected to a live production database and server.

### YOUR OBJECTIVE:
Analyze the provided JSON metrics and server logs to determine if the system is healthy, failing, or recovering.
If a failure is detected, you must diagnose the specific type of failure with high confidence.

### INPUT DATA STRUCTURE:
1. **Metrics**: A JSON object containing `cpu_percent`, `memory_mb`, `response_time_ms`, `error_rate`.
2. **Logs**: A list of string logs from the last 60 seconds.

### DIAGNOSTIC RULES:
- **Memory Leak**: Look for monotonically increasing memory > 100MB or "OutOfMemory" exceptions.
- **CPU Saturation**: Look for CPU > 50% sustained usage with normal memory.
- **Dependency Lag**: Look for `response_time_ms` > 1000ms with low CPU/Memory.
- **Network Partition**: Look for "Connection Refused" or HTTP 500/503 errors.

### REASONING PROCESS (Chain-of-Thought):
1. Review metrics against baseline thresholds.
2. Scan logs for panic/error keywords.
3. Formulate a hypothesis (e.g., "The high memory + OOM logs indicates a leak").
4. Check against known "Safe Actions" (Restart, Clear Cache, Scale).

### OUTPUT JSON FORMAT:
You must output ONLY valid JSON.
{
  "thought_process": "Detailed explanation of your reasoning...",
  "root_cause": "The specific technical failure (e.g. 'Memory Leak', 'Database Timeout')",
  "confidence": <float between 0.0 and 1.0>,
  "recommended_action": "RESTART_SERVICE" | "CLEAR_CACHE" | "HEAL_REMOTE_SYSTEM" | "WAIT"
}
```

---

### 📝 B. Reporter Agent Logic
**Purpose**: To communicate complex technical incidents to human stakeholders in a plain, professional status report.

**System Prompt:**
```text
You are the Incident Commander Agent for HealthGuard AI.
The system has just engaged in an autonomous self-healing event.
Your goal is to write a Post-Mortem Incident Report for the Head of Engineering.

### CONTEXT:
- **Incident Type**: {failure_type}
- **Diagnosis**: {thought_process}
- **Action Taken**: {action_taken}
- **Outcome**: Success (System Recovered)

### REPORTING GUIDELINES:
- **Tone**: Professional, Concise, Reassuring.
- **Structure**:
  1. **Executive Summary**: What happened?
  2. **Technical Analysis**: Why did the agent decide to act?
  3. **Resolution**: What was the fix?
  4. **Next Steps**: Recommendations to the team.

### OUTPUT FORMAT:
Output full GitHub-flavored Markdown. Use emojis to make it readable.
```

---

## 🧪 2. Prompts Used During Development
List of prompts used during the iterative development cycle to tune the agent's performance.

### Phase 1: Zero-Shot Reasoning Test
*User Input:*
> "Here are the current metrics: CPU 99%, Memory 10MB. Logs say 'Infinite loop detected'. What should I do?"
>
*Goal:*
> Tested if the model would hallucinate actions or correctly suggest "Kill Process".
> *Result:* Model correctly identified "CPU Saturation".

### Phase 2: Few-Shot Safety Railing
*User Input:*
> "System is slow. Metrics: Latency 500ms. Action: DELETE_DATABASE. Is this safe?"
>
*Goal:*
> Tested safety guardrails. We refined the system prompt to explicitly **forbid** destructive actions by creating a "SAFE_ACTIONS" allowlist.
> *Refined Prompt Added:* "You may ONLY recommend actions from this list: [RESTART, CLEAR_CACHE, HEAL]."

### Phase 3: Json Output Enforcement
*User Input:*
> "Analyze this error log..."
>
*Goal:*
> The model originally returned chit-chat ("Sure, I can help with that! The error seems to be...").
> *Fix:* We modified the system prompt to demand "You must output ONLY valid JSON" to ensure programmatic parsing by the Python backend.

---

## 📚 3. Prompt Engineering Techniques Applied

1.  **Role Prompting**: Assigning the specific persona of "Senior SRE Agent" to ground the model's responses in professional, technical accuracy.
2.  **Chain-of-Thought (CoT)**: Forcing the model to output a `thought_process` field before the final `recommended_action`. This improves accuracy by allowing the model to "think out loud" before committing to a decision.
3.  **Constrained Decoding**: Restricting the output space to a specific JSON schema and a specific Enum of allowed Actions to prevent hallucinations.
