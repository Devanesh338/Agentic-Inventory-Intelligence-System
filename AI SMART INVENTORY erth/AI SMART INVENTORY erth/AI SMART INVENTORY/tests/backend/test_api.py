from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "AEMIIF Backend"}

def test_regions():
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    regions = response.json()
    assert isinstance(regions, list)

def test_optimization_and_analytics_flow():
    # Run optimization
    payload = {
        "user_query": "Optimize replenishment for Chennai-Central with budget 100000",
        "region": "Chennai-Central"
    }
    opt_resp = client.post("/api/v1/optimization/run", json=payload)
    assert opt_resp.status_code == 200, f"Optimization failed: {opt_resp.text}"
    opt_data = opt_resp.json()
    
    request_id = opt_data["request_id"]
    assert request_id
    assert "summary" in opt_data
    assert "procurement_plan" in opt_data
    assert "inventory_summary" in opt_data
    
    # Test all analytics endpoints
    endpoints = [
        "overview",
        "procurement",
        "demand-inventory",
        "suppliers",
        "capacity",
        "requirements",
        "constraints",
        "optimization",
        "explanation"
    ]
    for ep in endpoints:
        res = client.get(f"/api/v1/analytics/{ep}/{request_id}")
        assert res.status_code == 200, f"Analytics endpoint {ep} returned {res.status_code}: {res.text}"
    
    # Test approval
    approve_resp = client.post(f"/api/v1/approval/{request_id}/approve", json={"approved_by": "tester", "comment": "looks good"})
    assert approve_resp.status_code == 200
    assert approve_resp.json()["approval_status"] == "APPROVED"
    
    # Test rejection
    reject_resp = client.post(f"/api/v1/approval/{request_id}/reject", json={"rejected_by": "tester", "reason": "budget check"})
    assert reject_resp.status_code == 200
    assert reject_resp.json()["approval_status"] == "REJECTED"
