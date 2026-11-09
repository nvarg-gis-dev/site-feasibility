import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

INSIDE_POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [-79.616, 8.929], [-79.614, 8.929],
        [-79.614, 8.931], [-79.616, 8.931], [-79.616, 8.929],
    ]],
}
PARTIALLY_OUTSIDE_POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [-79.605, 8.929], [-79.590, 8.929],
        [-79.590, 8.931], [-79.605, 8.931], [-79.605, 8.929],
    ]],
}
FULLY_OUTSIDE_POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [-80.616, 8.929], [-80.614, 8.929],
        [-80.614, 8.931], [-80.616, 8.931], [-80.616, 8.929],
    ]],
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_assessment_inside_polygon():
    response = client.post("/assessment", json={"polygon": INSIDE_POLYGON})
    assert response.status_code == 200
    body = response.json()
    assert body["area_m2"] > 0
    assert body["elevation"]["min"] <= body["elevation"]["mean"] <= body["elevation"]["max"]
    assert body["slope"]["max_deg"] >= body["slope"]["mean_deg"] >= 0


def test_earthwork_inside_polygon():
    response = client.post(
        "/earthwork",
        json={"polygon": INSIDE_POLYGON, "platform_elev_m": 50.0, "unit_cost_usd": 10.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cut_m3"] >= 0
    assert body["fill_m3"] >= 0
    assert body["est_cost_usd"] == pytest.approx((body["cut_m3"] + body["fill_m3"]) * 10.0)


def test_earthwork_rejects_negative_unit_cost():
    response = client.post(
        "/earthwork",
        json={"polygon": INSIDE_POLYGON, "platform_elev_m": 50.0, "unit_cost_usd": -1.0},
    )
    assert response.status_code == 422


def test_assessment_polygon_partially_outside_dem():
    response = client.post("/assessment", json={"polygon": PARTIALLY_OUTSIDE_POLYGON})
    assert response.status_code == 422
    assert "fully inside" in response.json()["detail"].lower()


def test_assessment_polygon_fully_outside_dem():
    response = client.post("/assessment", json={"polygon": FULLY_OUTSIDE_POLYGON})
    assert response.status_code == 422
    assert "fully inside" in response.json()["detail"].lower()


def test_cors_allows_vite_dev_origin():
    response = client.options(
        "/assessment",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
