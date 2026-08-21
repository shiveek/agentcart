from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Test root GET /health endpoint returns 200 and expected health JSON schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AgentCart API"
    assert data["version"] == "0.1.0"


def test_api_v1_health_endpoint() -> None:
    """Test /api/v1/health endpoint returns 200 and expected health JSON schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AgentCart API"
    assert data["version"] == "0.1.0"
