from fastapi.testclient import TestClient

from app.main import app


def test_health_is_loopback_safe_and_reports_environment() -> None:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "sandbox"}
