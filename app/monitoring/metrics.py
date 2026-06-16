"""
HealthGuard AI — Prometheus Metrics Definitions
Exposes application metrics for Prometheus scraping and Grafana dashboards.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest


# ── Application Info ─────────────────────────────────────────
APP_INFO = Info("healthguard", "HealthGuard AI application metadata")
APP_INFO.info({
    "version": "2.0.0",
    "component": "control_plane",
})

# ── Incident Metrics ─────────────────────────────────────────
INCIDENTS_DETECTED = Counter(
    "healthguard_incidents_detected_total",
    "Total number of anomalies detected by the Monitor Agent",
    ["failure_type"]
)

INCIDENTS_RESOLVED = Counter(
    "healthguard_incidents_resolved_total",
    "Total number of incidents successfully resolved",
    ["failure_type", "action_taken"]
)

INCIDENTS_FAILED = Counter(
    "healthguard_incidents_failed_total",
    "Total incidents where auto-fix failed",
    ["failure_type"]
)

ACTIVE_INCIDENTS = Gauge(
    "healthguard_active_incidents",
    "Number of currently active (unresolved) incidents"
)

# ── Agent Performance Metrics ────────────────────────────────
DIAGNOSIS_DURATION = Histogram(
    "healthguard_diagnosis_duration_seconds",
    "Time taken by DiagnosticianAgent to analyze and diagnose",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

FIX_DURATION = Histogram(
    "healthguard_fix_duration_seconds",
    "Time taken by FixerAgent to execute a fix",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

AGENT_ACTIONS = Counter(
    "healthguard_agent_actions_total",
    "Total actions performed by agents",
    ["agent", "action_type"]
)

DIAGNOSIS_CONFIDENCE = Histogram(
    "healthguard_diagnosis_confidence",
    "Distribution of diagnosis confidence scores",
    buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0]
)

# ── Target System Metrics ────────────────────────────────────
TARGET_CPU = Gauge(
    "healthguard_target_cpu_percent",
    "Current CPU usage of the monitored target system"
)

TARGET_MEMORY = Gauge(
    "healthguard_target_memory_mb",
    "Current memory usage of the monitored target system (MB)"
)

TARGET_LATENCY = Gauge(
    "healthguard_target_response_time_ms",
    "Current response time of the monitored target system (ms)"
)

TARGET_ERROR_RATE = Gauge(
    "healthguard_target_error_rate_percent",
    "Current error rate of the monitored target system (%)"
)

TARGET_UP = Gauge(
    "healthguard_target_up",
    "Whether the target system is reachable (1=up, 0=down)"
)

# ── System Stats ─────────────────────────────────────────────
FIX_SUCCESS_RATE = Gauge(
    "healthguard_fix_success_rate_percent",
    "Overall fix success rate percentage"
)

MTTR_SECONDS = Gauge(
    "healthguard_mttr_seconds",
    "Mean Time To Resolve (MTTR) in seconds"
)

LLM_REQUESTS = Counter(
    "healthguard_llm_requests_total",
    "Total LLM API requests made",
    ["provider", "status"]  # status: success, error, fallback
)

LLM_LATENCY = Histogram(
    "healthguard_llm_latency_seconds",
    "LLM API response latency",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)


def get_prometheus_metrics() -> bytes:
    """Generate Prometheus text format metrics for scraping."""
    return generate_latest()
