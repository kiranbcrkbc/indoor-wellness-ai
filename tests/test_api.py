import os
import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["software_only_mode"] is True
    assert data["hardware_required"] is False


def test_api_list_shelves():
    res = client.get("/api/shelves")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_create_shelf():
    payload = {
        "name": "Integration Test Shelf",
        "roi_coordinates": [[50, 50], [300, 300]],
        "expected_capacity": 6,
        "low_stock_threshold": 0.35,
        "empty_threshold": 0.05
    }
    res = client.post("/api/shelves", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Integration Test Shelf"
    assert data["shelf_id"] is not None


def test_api_detect_demo_scenario():
    res = client.post("/api/detect/demo?scenario=full")
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "demo"
    assert data["scenario"] == "full"
    assert "shelf_statuses" in data
    assert "annotated_image_url" in data
    assert data["annotated_image_url"].startswith("data:image/jpeg;base64,")


def test_api_environmental_latest():
    res = client.get("/api/environmental/latest")
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "SOFTWARE SIMULATION"
    assert "raw" in data
    assert "kalman_filtered" in data
    assert "prediction" in data


def test_api_environmental_manual():
    payload = {
        "pm25": 45.0,
        "co2": 950.0,
        "voc": 220.0,
        "temperature": 24.5,
        "humidity": 55.0
    }
    res = client.post("/api/environmental/manual", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "MANUAL ENTRY"
    assert "prediction" in data


def test_api_settings():
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "confidence_threshold" in data
    assert "low_stock_threshold" in data


def test_api_model_info():
    res = client.get("/api/settings/model/info")
    assert res.status_code == 200
    data = res.json()
    assert "model_name" in data
    assert "framework" in data


def test_api_live_camera():
    res = client.post("/api/detect/live/start?camera_index=0")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["ready", "unavailable"]
    if data["status"] == "unavailable":
        assert "message" in data


def test_api_detect_image_upload():
    image_path = "fixtures/shelf_low.jpg"
    if not os.path.exists(image_path):
        from backend.app.api.detect import generate_synthetic_shelf_image
        import cv2
        img = generate_synthetic_shelf_image("low")
        cv2.imwrite(image_path, img)

    with open(image_path, "rb") as f:
        res = client.post("/api/detect/image", files={"file": ("shelf_low.jpg", f, "image/jpeg")})
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "image"
    assert "shelf_statuses" in data
    assert "annotated_image_url" in data


def test_api_detect_video_upload():
    video_path = "fixtures/sample_shelf_video.mp4"
    assert os.path.exists(video_path), "Sample video fixture missing"

    with open(video_path, "rb") as f:
        res = client.post("/api/detect/video", files={"file": ("sample_shelf_video.mp4", f, "video/mp4")})
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "video"
    assert data["frames_sampled"] > 0
    assert "shelf_statuses" in data


def test_api_detect_invalid_file():
    # Attempt to upload an invalid file extension (e.g. .txt)
    dummy_text = io.BytesIO(b"not an image file")
    res = client.post("/api/detect/image", files={"file": ("invalid.txt", dummy_text, "text/plain")})
    assert res.status_code == 400


def test_api_environmental_scenario():
    res = client.post("/api/environmental/scenario?scenario=Hazardous+Event")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["scenario"] == "Hazardous Event"

    # Reset back to Normal Indoor
    client.post("/api/environmental/scenario?scenario=Normal+Indoor")


def test_api_environmental_upload_csv():
    csv_path = "fixtures/sample_environmental_data.csv"
    assert os.path.exists(csv_path)
    with open(csv_path, "rb") as f:
        res = client.post("/api/environmental/upload", files={"file": ("sample.csv", f, "text/csv")})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["readings_imported"] > 0


def test_api_environmental_upload_json():
    json_path = "fixtures/sample_readings.json"
    assert os.path.exists(json_path)
    with open(json_path, "rb") as f:
        res = client.post("/api/environmental/upload", files={"file": ("sample.json", f, "application/json")})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["readings_imported"] > 0


def test_api_environmental_upload_invalid():
    dummy = io.BytesIO(b"unsupported content")
    res = client.post("/api/environmental/upload", files={"file": ("test.pdf", dummy, "application/pdf")})
    assert res.status_code == 400


def test_api_environmental_history():
    res = client.get("/api/environmental/history?limit=15")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        assert "pm25" in data[0]
        assert "co2" in data[0]
        assert "timestamp" in data[0]


def test_api_alerts_lifecycle():
    # 1. Fetch alerts
    res = client.get("/api/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)

    # 2. Filter by severity
    res_crit = client.get("/api/alerts?severity=CRITICAL")
    assert res_crit.status_code == 200
    for a in res_crit.json():
        assert a["severity"] == "CRITICAL"

    # 3. Resolve single alert if present
    if alerts:
        target_id = alerts[0]["alert_id"]
        res_res = client.post(f"/api/alerts/{target_id}/resolve")
        assert res_res.status_code == 200
        assert res_res.json()["is_resolved"] is True

    # 4. Resolve all
    res_all = client.post("/api/alerts/resolve-all")
    assert res_all.status_code == 200
    assert "resolved_count" in res_all.json()


def test_api_analytics_summary_and_export():
    # Summary
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "shelf_distribution" in data
    assert "product_distribution" in data

    # Export CSV
    res_csv = client.get("/api/analytics/export")
    assert res_csv.status_code == 200
    assert res_csv.headers["content-type"].startswith("text/csv")
    assert "Run ID,Input Type,Source,Shelf Name" in res_csv.text


def test_api_shelf_crud_lifecycle():
    # Create
    new_shelf = {
        "name": "CRUD Test Shelf",
        "roi_coordinates": [[10, 10], [200, 200]],
        "expected_capacity": 5,
        "low_stock_threshold": 0.3,
        "empty_threshold": 0.05
    }
    res = client.post("/api/shelves", json=new_shelf)
    assert res.status_code == 201
    shelf_id = res.json()["shelf_id"]

    # Update
    update_payload = {"name": "CRUD Test Shelf Updated", "expected_capacity": 7}
    res_up = client.put(f"/api/shelves/{shelf_id}", json=update_payload)
    assert res_up.status_code == 200
    assert res_up.json()["name"] == "CRUD Test Shelf Updated"
    assert res_up.json()["expected_capacity"] == 7

    # Delete
    res_del = client.delete(f"/api/shelves/{shelf_id}")
    assert res_del.status_code == 200

    # Verify deleted
    res_del2 = client.delete(f"/api/shelves/{shelf_id}")
    assert res_del2.status_code == 404


def test_api_update_settings():
    res = client.put("/api/settings", json={"confidence_threshold": "0.50"})
    assert res.status_code == 200
    assert "confidence_threshold" in res.json()["updated_keys"]

    res_get = client.get("/api/settings")
    assert res_get.json()["confidence_threshold"] == "0.50"

