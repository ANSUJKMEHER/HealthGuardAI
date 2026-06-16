"""
Tests for API endpoints.
Verifies all REST endpoints return correct responses.
"""


def test_root_endpoint(client):
    """Test root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "HealthGuard AI"
    assert data["version"] == "2.0.0"


def test_health_check(client):
    """Test health check endpoint for deployment platforms."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "engine_running" in data


def test_system_status(client):
    """Test system status endpoint."""
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "engine_running" in data
    assert "stats" in data
    assert "total_incidents" in data["stats"]


def test_start_stop_system(client):
    """Test system start and stop lifecycle."""
    # Start
    response = client.post("/api/v1/system/start")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

    # Start again (should say already running)
    response = client.post("/api/v1/system/start")
    assert response.status_code == 200

    # Stop
    response = client.post("/api/v1/system/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "stopped"


def test_metrics_requires_running(client):
    """Test that metrics endpoint requires system to be running."""
    # Stop system first
    client.post("/api/v1/system/stop")

    response = client.get("/api/v1/metrics")
    assert response.status_code == 400


def test_incidents_endpoint(client):
    """Test incidents listing."""
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_incidents_stats(client):
    """Test incident statistics endpoint."""
    response = client.get("/api/v1/incidents/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_incidents" in data
    assert "success_rate" in data


def test_prometheus_metrics(client):
    """Test Prometheus metrics endpoint returns valid format."""
    response = client.get("/metrics/prometheus")
    assert response.status_code == 200
    content = response.text
    # Prometheus metrics should contain our custom metrics
    assert "healthguard" in content


def test_export_incidents(client):
    """Test incident export as JSON download."""
    response = client.get("/api/v1/export/incidents")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_inject_failure_requires_running(client):
    """Test that failure injection requires running system."""
    client.post("/api/v1/system/stop")
    response = client.post("/api/v1/inject_failure", json={"type": "MEMORY_LEAK"})
    assert response.status_code == 400


def test_monitor_url_update(client):
    """Test updating the monitoring target URL."""
    response = client.post("/api/v1/monitor/url", json={"url": "http://example.com/api"})
    assert response.status_code == 200


def test_legacy_endpoints(client):
    """Test backward-compatible legacy endpoints still work."""
    response = client.get("/incidents")
    assert response.status_code == 200

    response = client.post("/system/stop")
    assert response.status_code == 200
