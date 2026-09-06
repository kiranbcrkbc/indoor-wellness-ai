"""
Automated Live Deployment Verification Suite (Sections 11 - 20)
Tests all features directly against the REAL PERMANENT PUBLIC HTTPS URL:
https://indoor-wellness-ai.onrender.com
"""

import os
import io
import time
import requests
import pytest

LIVE_URL = os.environ.get("LIVE_DEPLOYMENT_URL", "https://indoor-wellness-ai.onrender.com")


class TimeoutAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, timeout=60, *args, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, *args, **kwargs):
        kwargs["timeout"] = kwargs.get("timeout", self.timeout)
        return super().send(*args, **kwargs)


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.mount("https://", TimeoutAdapter(timeout=60))
    s.mount("http://", TimeoutAdapter(timeout=60))
    s.headers.update({"User-Agent": "IndoorWellnessAI-LiveValidator/1.0"})
    return s


def test_11_live_pages_and_static_assets(session):
    """Section 11: Test live website page, layout, JS, CSS, vendor assets over HTTPS."""
    # Root dashboard
    res_root = session.get(f"{LIVE_URL}/")
    assert res_root.status_code == 200, f"Root dashboard failed: {res_root.status_code}"
    html = res_root.text
    assert "Indoor Wellness & Smart Shelf AI Platform" in html
    assert "Executive Overview" in html
    assert "Smart Shelf Vision" in html
    assert "Indoor Wellness AI" in html
    assert "Shelf Manager" in html
    assert "Alert Center" in html
    assert "Analytics & Export" in html
    assert "System & Model" in html

    # Static assets
    assets = [
        "/static/css/style.css",
        "/static/js/app.js",
        "/static/vendor/chart.umd.min.js",
        "/static/vendor/feather.min.js"
    ]
    for asset in assets:
        res_asset = session.get(f"{LIVE_URL}{asset}")
        assert res_asset.status_code == 200, f"Failed to load asset: {asset}"
        assert len(res_asset.content) > 1000, f"Asset content suspiciously empty: {asset}"


def test_12_live_ai_model_image_and_video(session):
    """Section 12: Real AI inference on public website via image and video uploads."""
    # 1. Preset demo AI execution
    res_demo = session.post(f"{LIVE_URL}/api/detect/demo?scenario=full")
    assert res_demo.status_code == 200
    data_demo = res_demo.json()
    assert data_demo["input_type"] == "demo"
    assert "shelf_statuses" in data_demo
    assert "annotated_image_url" in data_demo
    assert data_demo["annotated_image_url"].startswith("data:image/jpeg;base64,")
    assert data_demo["processing_time_ms"] > 0

    # 2. Image upload inference
    image_path = "fixtures/shelf_low.jpg"
    assert os.path.exists(image_path), "Test fixture missing"
    with open(image_path, "rb") as f:
        res_img = session.post(f"{LIVE_URL}/api/detect/image", files={"file": ("shelf_low.jpg", f, "image/jpeg")})
    assert res_img.status_code == 200
    data_img = res_img.json()
    assert data_img["input_type"] == "image"
    assert "shelf_statuses" in data_img
    assert "annotated_image_url" in data_img

    # 3. Video upload inference (FR-10)
    video_path = "fixtures/sample_shelf_video.mp4"
    assert os.path.exists(video_path), "Video fixture missing"
    with open(video_path, "rb") as f:
        res_vid = session.post(f"{LIVE_URL}/api/detect/video", files={"file": ("sample_shelf_video.mp4", f, "video/mp4")})
    assert res_vid.status_code == 200
    data_vid = res_vid.json()
    assert data_vid["input_type"] == "video"
    assert data_vid["frames_sampled"] > 0
    assert "shelf_statuses" in data_vid


def test_13_live_camera_fallback(session):
    """Section 13: Optional live camera check with clean non-crashing fallback."""
    res_cam = session.post(f"{LIVE_URL}/api/detect/live/start?camera_index=0")
    assert res_cam.status_code == 200
    data_cam = res_cam.json()
    assert data_cam["status"] in ["ready", "unavailable"]
    if data_cam["status"] == "unavailable":
        assert "message" in data_cam
        assert "not detected" in data_cam["message"].lower() or "webcam" in data_cam["message"].lower()


def test_14_live_environmental_ai(session):
    """Section 14: Environmental simulation, Kalman filtering, EPA AQI, ANN forecast, and ventilation recommendation."""
    # 1. Telemetry step
    res_step = session.get(f"{LIVE_URL}/api/environmental/latest")
    assert res_step.status_code == 200
    data_step = res_step.json()
    assert "raw" in data_step
    assert "kalman_filtered" in data_step
    assert "prediction" in data_step

    pred = data_step["prediction"]
    assert "current_aqi" in pred
    assert "category" in pred
    assert "forecast_1h" in pred
    assert "forecast_3h" in pred
    assert "forecast_6h" in pred
    assert "ventilation_recommendation" in pred
    assert "actuator_power_level" in pred

    # 2. Scenario change
    res_scen = session.post(f"{LIVE_URL}/api/environmental/scenario?scenario=Hazardous+Event")
    assert res_scen.status_code == 200
    assert res_scen.json()["status"] == "success"

    # Reset back to Normal
    session.post(f"{LIVE_URL}/api/environmental/scenario?scenario=Normal+Indoor")


def test_15_live_database_crud_and_persistence(session):
    """Section 15: Perform real CRUD database operations over the public HTTPS API."""
    # CREATE
    new_shelf = {
        "name": "Live Cloud QA Shelf",
        "roi_coordinates": [[20, 20], [300, 300]],
        "expected_capacity": 6,
        "low_stock_threshold": 0.35,
        "empty_threshold": 0.05
    }
    res_create = session.post(f"{LIVE_URL}/api/shelves", json=new_shelf)
    assert res_create.status_code == 201
    shelf_id = res_create.json()["shelf_id"]

    # READ
    res_list = session.get(f"{LIVE_URL}/api/shelves")
    assert res_list.status_code == 200
    shelves = res_list.json()
    assert any(s["shelf_id"] == shelf_id for s in shelves)

    # UPDATE
    update_payload = {"name": "Live Cloud QA Shelf - Modified", "expected_capacity": 10}
    res_up = session.put(f"{LIVE_URL}/api/shelves/{shelf_id}", json=update_payload)
    assert res_up.status_code == 200
    assert res_up.json()["name"] == "Live Cloud QA Shelf - Modified"
    assert res_up.json()["expected_capacity"] == 10

    # DELETE
    res_del = session.delete(f"{LIVE_URL}/api/shelves/{shelf_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "success"


def test_16_live_file_inputs_and_error_handling(session):
    """Section 16: Test CSV/JSON file ingestion and robust error handling."""
    # 1. CSV ingestion
    with open("fixtures/sample_environmental_data.csv", "rb") as f:
        res_csv = session.post(f"{LIVE_URL}/api/environmental/upload", files={"file": ("test.csv", f, "text/csv")})
    assert res_csv.status_code == 200
    assert res_csv.json()["status"] == "success"
    assert res_csv.json()["readings_imported"] > 0

    # 2. JSON ingestion
    with open("fixtures/sample_readings.json", "rb") as f:
        res_json = session.post(f"{LIVE_URL}/api/environmental/upload", files={"file": ("test.json", f, "application/json")})
    assert res_json.status_code == 200
    assert res_json.json()["status"] == "success"
    assert res_json.json()["readings_imported"] > 0

    # 3. Invalid file format (Error handling)
    dummy = io.BytesIO(b"corrupted or unsupported format")
    res_inv = session.post(f"{LIVE_URL}/api/environmental/upload", files={"file": ("bad.exe", dummy, "application/octet-stream")})
    assert res_inv.status_code == 400


def test_17_live_alerts_lifecycle(session):
    """Section 17: Trigger, filter, inspect, and resolve alerts over public HTTPS."""
    # Trigger low stock / empty via demo
    session.post(f"{LIVE_URL}/api/detect/demo?scenario=empty")

    # Fetch alerts
    res_alerts = session.get(f"{LIVE_URL}/api/alerts?limit=20")
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()
    assert isinstance(alerts, list)
    assert len(alerts) > 0

    # Resolve an alert
    alert_to_resolve = alerts[0]["alert_id"]
    res_res = session.post(f"{LIVE_URL}/api/alerts/{alert_to_resolve}/resolve")
    assert res_res.status_code == 200
    assert res_res.json()["is_resolved"] is True

    # Bulk resolve
    res_bulk = session.post(f"{LIVE_URL}/api/alerts/resolve-all")
    assert res_bulk.status_code == 200


def test_18_live_analytics_and_export(session):
    """Section 18: Validate analytics KPIs and CSV audit download on live server."""
    # KPIs
    res_summary = session.get(f"{LIVE_URL}/api/analytics/summary")
    assert res_summary.status_code == 200
    data = res_summary.json()
    assert "kpis" in data
    assert "total_runs" in data["kpis"]
    assert "shelf_distribution" in data
    assert "product_distribution" in data

    # Export CSV
    res_export = session.get(f"{LIVE_URL}/api/analytics/export")
    assert res_export.status_code == 200
    assert "text/csv" in res_export.headers.get("content-type", "")
    assert "Run ID" in res_export.text


def test_19_20_live_resilience_and_performance(session):
    """Section 19 & 20: Test edge-case error recovery and live response latency."""
    # 1. Missing shelf update -> 404 Not Found
    res_404 = session.get(f"{LIVE_URL}/api/shelves/999999")
    assert res_404.status_code in [404, 405]

    # 2. Invalid scenario -> 400 Bad Request
    res_bad_scen = session.post(f"{LIVE_URL}/api/environmental/scenario?scenario=NonExistentScenario")
    assert res_bad_scen.status_code == 400

    # 3. Model Info endpoint latency benchmark
    t0 = time.perf_counter()
    res_info = session.get(f"{LIVE_URL}/api/settings/model/info")
    latency_ms = (time.perf_counter() - t0) * 1000.0
    assert res_info.status_code == 200
    assert latency_ms < 1500.0, f"Public HTTPS response too slow: {latency_ms:.1f} ms"
