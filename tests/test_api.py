from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "DataGuardian AI"
    assert data["status"] == "running"
    assert data["version"] == "1.1.0"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy"
    }


def test_investigate_unknown_run_returns_404():
    response = client.post(
        "/investigate",
        json={
            "run_id": 999999
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert (
        "was not found"
        in data["detail"]
    )