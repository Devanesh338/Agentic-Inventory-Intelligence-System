from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "AEMIIF Backend"}

def test_regions():
    # Will return empty if DB is mocked, but should be 200 OK
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
