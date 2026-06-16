"""
HealthGuard AI — Test Fixtures
Shared test configuration, database fixtures, and mock providers.
"""

import os
import pytest
from unittest.mock import MagicMock

# Force test configuration before any app imports
os.environ["DATABASE_URL"] = "sqlite:///./test_healthguard.db"
os.environ["LLM_PROVIDER"] = "fallback"
os.environ["TARGET_URL"] = "http://127.0.0.1:3000/api"

from fastapi.testclient import TestClient
from app.server import app
from app.database.session import init_db, engine
from app.database.models import Base


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()  # Release all connections before deleting file
    # Clean up test DB file
    try:
        if os.path.exists("test_healthguard.db"):
            os.remove("test_healthguard.db")
    except PermissionError:
        pass  # Windows may still hold the file; it's a test artifact


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_llm():
    """Mock LLM provider for testing without API calls."""
    provider = MagicMock()
    provider.analyze_anomaly.return_value = {
        "thought_process": "Test diagnosis: Memory leak detected",
        "root_cause": "Test Memory Leak",
        "confidence": 0.95,
        "recommended_action": "HEAL_REMOTE_SYSTEM",
    }
    provider.generate_report.return_value = "# Test Report\nIncident resolved."
    return provider


@pytest.fixture
def sample_metrics():
    """Sample metrics data for testing."""
    return {
        "cpu_percent": 15.0,
        "memory_mb": 30.0,
        "error_rate_percent": 0.0,
        "response_time_ms": 50.0,
    }


@pytest.fixture
def anomaly_metrics():
    """Metrics that should trigger anomaly detection."""
    return {
        "cpu_percent": 85.0,
        "memory_mb": 250.0,
        "error_rate_percent": 15.0,
        "response_time_ms": 5000.0,
    }
