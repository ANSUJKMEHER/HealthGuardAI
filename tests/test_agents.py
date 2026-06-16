"""
Tests for agent logic.
Verifies anomaly detection, safety guardrails, and diagnosis accuracy.
"""

from app.llm.fallback_provider import FallbackProvider


class TestFallbackProvider:
    """Test the rule-based fallback LLM provider."""

    def setup_method(self):
        self.provider = FallbackProvider()

    def test_detects_memory_leak(self):
        """Should diagnose memory leak when memory > 100MB."""
        metrics = {"cpu_percent": 15, "memory_mb": 250, "error_rate_percent": 0, "response_time_ms": 50}
        result = self.provider.analyze_anomaly(metrics, [])
        assert result["root_cause"] == "Application Memory Leak"
        assert result["confidence"] >= 0.9
        assert result["recommended_action"] == "HEAL_REMOTE_SYSTEM"

    def test_detects_oom_from_logs(self):
        """Should detect OOM from log messages."""
        metrics = {"cpu_percent": 15, "memory_mb": 50, "error_rate_percent": 0, "response_time_ms": 50}
        logs = [{"timestamp": "12:00:00", "level": "ERROR", "message": "OutOfMemoryError in heap space"}]
        result = self.provider.analyze_anomaly(metrics, logs)
        assert "Memory Leak" in result["root_cause"]
        assert result["confidence"] >= 0.99
        assert result["recommended_action"] == "RESTART_SERVICE"

    def test_detects_cpu_spike(self):
        """Should diagnose CPU saturation when CPU > 50%."""
        metrics = {"cpu_percent": 85, "memory_mb": 30, "error_rate_percent": 0, "response_time_ms": 50}
        result = self.provider.analyze_anomaly(metrics, [])
        assert "CPU" in result["root_cause"]
        assert result["confidence"] >= 0.9

    def test_detects_server_crash(self):
        """Should diagnose HTTP 500 errors from logs."""
        metrics = {"cpu_percent": 10, "memory_mb": 30, "error_rate_percent": 0, "response_time_ms": 50}
        logs = [{"timestamp": "12:00:00", "level": "ERROR", "message": "HTTP 500 Internal Server Error"}]
        result = self.provider.analyze_anomaly(metrics, logs)
        assert "Crash" in result["root_cause"] or "5xx" in result["root_cause"]
        assert result["recommended_action"] == "HEAL_REMOTE_SYSTEM"

    def test_detects_high_latency(self):
        """Should diagnose high latency."""
        metrics = {"cpu_percent": 10, "memory_mb": 30, "error_rate_percent": 0, "response_time_ms": 6000}
        result = self.provider.analyze_anomaly(metrics, [])
        assert "Timeout" in result["root_cause"] or "Latency" in result["root_cause"]
        assert result["confidence"] >= 0.9

    def test_detects_rate_limiting(self):
        """Should diagnose 429 rate limiting."""
        metrics = {"cpu_percent": 10, "memory_mb": 30, "error_rate_percent": 0, "response_time_ms": 50}
        logs = [{"timestamp": "12:00:00", "level": "WARN", "message": "HTTP 429 Too Many Requests"}]
        result = self.provider.analyze_anomaly(metrics, logs)
        assert "Rate Limit" in result["root_cause"]

    def test_normal_system_returns_wait(self):
        """Should return WAIT for healthy metrics."""
        metrics = {"cpu_percent": 10, "memory_mb": 30, "error_rate_percent": 0, "response_time_ms": 50}
        result = self.provider.analyze_anomaly(metrics, [])
        assert result["root_cause"] == "None"
        assert result["recommended_action"] == "WAIT"
        assert result["confidence"] == 1.0

    def test_diagnosis_has_required_keys(self):
        """Every diagnosis should have all required keys."""
        metrics = {"cpu_percent": 85, "memory_mb": 250, "error_rate_percent": 50, "response_time_ms": 5000}
        result = self.provider.analyze_anomaly(metrics, [])
        assert "thought_process" in result
        assert "root_cause" in result
        assert "confidence" in result
        assert "recommended_action" in result
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_report_generation(self):
        """Should generate a non-empty report."""
        incident_data = {
            "failure_type": "Memory Leak",
            "timestamp": "2024-01-01 12:00:00",
            "diagnosis": {"root_cause": "Memory Leak", "confidence": 0.95, "thought_process": "Test"},
            "action_taken": "RESTART_SERVICE",
            "recovered": True,
        }
        report = self.provider.generate_report(incident_data)
        assert len(report) > 100
        assert "Memory Leak" in report
        assert "RESOLVED" in report


class TestFixerSafety:
    """Test fixer agent safety guardrails."""

    def test_safe_actions_defined(self):
        """Verify SAFE_ACTIONS allowlist exists."""
        from app.agents.fixer import FixerAgent
        assert "RESTART_SERVICE" in FixerAgent.SAFE_ACTIONS
        assert "CLEAR_CACHE" in FixerAgent.SAFE_ACTIONS
        assert "HEAL_REMOTE_SYSTEM" in FixerAgent.SAFE_ACTIONS
        # Dangerous actions should NOT be in the list
        assert "DELETE_DATABASE" not in FixerAgent.SAFE_ACTIONS
        assert "DROP_TABLE" not in FixerAgent.SAFE_ACTIONS
