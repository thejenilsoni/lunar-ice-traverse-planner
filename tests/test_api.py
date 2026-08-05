from fastapi.testclient import TestClient

from services.api.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_scene_endpoint():
    response = client.get("/v1/scene?seed=2026&size=32")
    assert response.status_code == 200
    payload = response.json()
    assert payload["size"] == 32
    assert "ice_probability" in payload["layers"]


def test_landing_site_endpoint():
    response = client.post("/v1/landing-sites/rank", json={"seed": 2026, "limit": 4})
    assert response.status_code == 200
    assert len(response.json()["sites"]) == 4


def test_traverse_endpoint():
    response = client.post(
        "/v1/traverses/plan",
        json={"origin": {"row": 4, "col": 4}, "seed": 2026, "battery_wh": 7000},
    )
    assert response.status_code == 200
    assert "path" in response.json()
    assert "estimated_energy_wh" in response.json()
