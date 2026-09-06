import os
import io
import time
import base64
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
import numpy as np
import cv2

from backend.app.db.database import get_db
from backend.app.db.models import DetectionRun, Detection, Inventory, Shelf, Alert, Product, SystemSetting
from backend.app.cv.detector import detector_instance
from backend.app.logic.stock_logic import (
    classify_stock_status, shelf_temporal_filter, StockClassification
)

router = APIRouter(prefix="/detect", tags=["Detection"])

# Ensure uploads and fixture directories exist
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
UPLOAD_DIR = os.path.join(BASE_DIR, "database", "uploads")
FIXTURE_DIR = os.path.join(BASE_DIR, "fixtures")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FIXTURE_DIR, exist_ok=True)


def get_active_shelves(db: Session) -> List[Dict[str, Any]]:
    """Retrieves all shelves formatted for CV detector."""
    shelves = db.query(Shelf).all()
    out = []
    for s in shelves:
        coords = []
        if s.roi_coordinates:
            try:
                coords = json.loads(s.roi_coordinates)
            except Exception:
                coords = []
        out.append({
            "shelf_id": s.shelf_id,
            "name": s.name,
            "roi_coordinates": coords,
            "expected_capacity": s.expected_capacity,
            "low_stock_threshold": s.low_stock_threshold,
            "empty_threshold": s.empty_threshold
        })
    return out


def frame_to_base64(frame: np.ndarray) -> str:
    """Encodes OpenCV BGR frame into base64 JPEG data URI."""
    success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def generate_synthetic_shelf_image(scenario: str = "full", width: int = 800, height: int = 500) -> np.ndarray:
    """
    Generates a realistic synthetic shelf test image with visual product items
    for self-contained demo testing without needing external files.
    """
    img = np.full((height, width, 3), 35, dtype=np.uint8)  # Dark textured background

    # Draw shelf racks
    shelf_y_positions = [200, 420]
    for y in shelf_y_positions:
        cv2.rectangle(img, (40, y), (width - 40, y + 15), (80, 80, 90), -1)
        cv2.rectangle(img, (40, y), (width - 40, y + 15), (140, 140, 150), 2)

    # Determine item distribution based on scenario
    # Shelf 1: (x: 60 to 740, y: 70 to 195)
    # Shelf 2: (x: 60 to 740, y: 280 to 415)
    colors = [
        (220, 120, 40),   # Orange juice / bottle
        (60, 180, 75),    # Green soda / snack
        (230, 25, 75),    # Red cereal box
        (0, 130, 200),    # Blue can
        (245, 130, 48)    # Yellow carton
    ]

    items = []
    if scenario == "full":
        # Shelf 1 full (8 items)
        for i in range(8):
            x = 80 + i * 80
            items.append((x, 90, 50, 105, colors[i % len(colors)]))
        # Shelf 2 full (8 items)
        for i in range(8):
            x = 80 + i * 80
            items.append((x, 305, 50, 110, colors[(i + 2) % len(colors)]))
    elif scenario == "low":
        # Shelf 1 low stock (2 items)
        items.append((120, 90, 50, 105, colors[0]))
        items.append((360, 90, 50, 105, colors[1]))
        # Shelf 2 normal (5 items)
        for i in range(5):
            x = 80 + i * 110
            items.append((x, 305, 50, 110, colors[(i + 1) % len(colors)]))
    elif scenario == "empty":
        # Shelf 1 empty (0 items)
        # Shelf 2 empty or 1 item
        items.append((500, 305, 50, 110, colors[3]))

    # Draw items with 3D bevel and label
    for x, y, bw, bh, col in items:
        cv2.rectangle(img, (x, y), (x + bw, y + bh), col, -1)
        cv2.rectangle(img, (x, y), (x + bw, y + bh), (255, 255, 255), 1)
        cv2.circle(img, (x + bw // 2, y + 20), 8, (255, 255, 255), -1)

    return img


@router.post("/image")
async def detect_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Uploads and runs product detection and shelf inventory assessment on a static image."""
    start_time = time.time()

    # Validate file type
    filename = file.filename.lower()
    valid_exts = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
    if not any(filename.endswith(ext) for ext in valid_exts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Supported formats: {', '.join(valid_exts)}"
        )

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image file.")

    shelves = get_active_shelves(db)

    # Run detection
    det_results = detector_instance.detect(frame, shelves)
    elapsed_ms = round((time.time() - start_time) * 1000, 1)

    # Persist detection run
    run = DetectionRun(
        input_type="image",
        source_reference=file.filename,
        model_version=detector_instance.model_name,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Save individual detections
    for det in det_results["detections"]:
        # Find or create product class
        prod_name = det["class_name"]
        prod = db.query(Product).filter(Product.name == prod_name).first()
        if not prod:
            prod = Product(name=prod_name, category="Packaged Goods")
            db.add(prod)
            db.commit()
            db.refresh(prod)

        db_det = Detection(
            run_id=run.run_id,
            shelf_id=det.get("shelf_id"),
            product_id=prod.product_id,
            confidence=det["confidence"],
            bbox_x=det["x"],
            bbox_y=det["y"],
            bbox_w=det["width"],
            bbox_h=det["height"],
            detected_at=datetime.utcnow()
        )
        db.add(db_det)

    # Process per-shelf stock level logic
    shelf_statuses = {}
    for s in shelves:
        sid = s["shelf_id"]
        count = det_results["shelf_counts"].get(sid, 0)
        status_info = classify_stock_status(
            detected_count=count,
            expected_capacity=s["expected_capacity"],
            low_stock_threshold=s["low_stock_threshold"],
            empty_threshold=s["empty_threshold"]
        )
        shelf_statuses[sid] = status_info

        # Record inventory status
        inv = Inventory(
            shelf_id=sid,
            run_id=run.run_id,
            detected_count=count,
            occupancy_ratio=status_info["occupancy_ratio"],
            status=status_info["status"],
            recorded_at=datetime.utcnow()
        )
        db.add(inv)

        # Trigger alerts if low stock or empty
        if status_info["status"] in [StockClassification.LOW_STOCK, StockClassification.EMPTY]:
            alert = Alert(
                alert_type="LOW_STOCK" if status_info["status"] == StockClassification.LOW_STOCK else "EMPTY_SHELF",
                shelf_id=sid,
                message=f"Shelf '{s['name']}' stock alert: Status is {status_info['status']} ({count}/{s['expected_capacity']} items)",
                severity=status_info["severity"],
                is_resolved=False
            )
            db.add(alert)

    db.commit()

    # Generate annotated image
    annotated = detector_instance.render_annotated_frame(
        frame, det_results["detections"], shelves, shelf_statuses
    )
    b64_image = frame_to_base64(annotated)

    return {
        "run_id": run.run_id,
        "input_type": "image",
        "source_reference": file.filename,
        "model_version": detector_instance.model_name,
        "total_detections": det_results["total_detections"],
        "detections": det_results["detections"],
        "class_counts": det_results["class_counts"],
        "shelf_statuses": shelf_statuses,
        "annotated_image_url": b64_image,
        "processing_time_ms": elapsed_ms
    }


@router.post("/demo")
def run_demo_scenario(scenario: str = Query("full", description="Scenario: full, low, empty"), db: Session = Depends(get_db)):
    """
    Executes a pre-staged demonstration scenario (Full Shelf, Low Stock, Empty Shelf)
    directly in software without requiring external user files.
    """
    start_time = time.time()
    shelves = get_active_shelves(db)

    # Generate synthetic image for scenario
    frame = generate_synthetic_shelf_image(scenario=scenario)

    det_results = detector_instance.detect(frame, shelves)
    elapsed_ms = round((time.time() - start_time) * 1000, 1)

    run = DetectionRun(
        input_type="demo",
        source_reference=f"Demo Scenario: {scenario.upper()}",
        model_version=detector_instance.model_name,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    shelf_statuses = {}
    for s in shelves:
        sid = s["shelf_id"]
        count = det_results["shelf_counts"].get(sid, 0)
        status_info = classify_stock_status(
            detected_count=count,
            expected_capacity=s["expected_capacity"],
            low_stock_threshold=s["low_stock_threshold"],
            empty_threshold=s["empty_threshold"]
        )
        shelf_statuses[sid] = status_info

        inv = Inventory(
            shelf_id=sid,
            run_id=run.run_id,
            detected_count=count,
            occupancy_ratio=status_info["occupancy_ratio"],
            status=status_info["status"],
            recorded_at=datetime.utcnow()
        )
        db.add(inv)

        if status_info["status"] in [StockClassification.LOW_STOCK, StockClassification.EMPTY]:
            alert = Alert(
                alert_type="LOW_STOCK" if status_info["status"] == StockClassification.LOW_STOCK else "EMPTY_SHELF",
                shelf_id=sid,
                message=f"DEMO ALERT: Shelf '{s['name']}' transitioned to {status_info['status']} ({count}/{s['expected_capacity']} items)",
                severity=status_info["severity"],
                is_resolved=False
            )
            db.add(alert)

    db.commit()

    annotated = detector_instance.render_annotated_frame(
        frame, det_results["detections"], shelves, shelf_statuses
    )
    b64_image = frame_to_base64(annotated)

    return {
        "run_id": run.run_id,
        "input_type": "demo",
        "scenario": scenario,
        "total_detections": det_results["total_detections"],
        "class_counts": det_results["class_counts"],
        "shelf_statuses": shelf_statuses,
        "annotated_image_url": b64_image,
        "processing_time_ms": elapsed_ms
    }


@router.post("/live/start")
def start_live_camera(camera_index: int = 0):
    """
    Attempts to initialize optional local webcam.
    If no webcam hardware exists, returns a graceful 503 response instead of crashing (FR-18).
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return {
            "status": "unavailable",
            "message": "Physical webcam device not detected. Please use Image Upload, Video Upload, or Preset Demo Scenarios.",
            "camera_index": camera_index
        }
    cap.release()
    return {
        "status": "ready",
        "session_id": f"live_cam_{int(time.time())}",
        "camera_index": camera_index
    }


@router.post("/video")
async def detect_video(
    file: UploadFile = File(...),
    sample_rate_fps: int = Query(1, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """
    FR-10 Video Input: Accepts video files, samples frames, runs YOLO detection,
    evaluates temporal shelf occupancy across frames, and logs inventory state.
    """
    start_time = time.time()
    filename = file.filename.lower()
    valid_exts = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    if not any(filename.endswith(ext) for ext in valid_exts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid video file format. Supported formats: {', '.join(valid_exts)}"
        )

    temp_path = os.path.join(UPLOAD_DIR, f"temp_{int(time.time())}_{file.filename}")
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded video file is empty.")

        with open(temp_path, "wb") as f:
            f.write(contents)

        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not decode video file stream.")

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(video_fps / sample_rate_fps))

        shelves = get_active_shelves(db)
        frames_processed = 0
        max_samples = 15
        frame_idx = 0
        all_class_counts: Dict[str, int] = {}
        shelf_counts_accum: Dict[int, List[int]] = {s["shelf_id"]: [] for s in shelves}
        last_annotated_b64 = ""
        last_det_results = None

        while cap.isOpened() and frames_processed < max_samples:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                det_results = detector_instance.detect(frame, shelves)
                last_det_results = det_results
                frames_processed += 1

                for sid, count in det_results["shelf_counts"].items():
                    shelf_counts_accum[sid].append(count)

                for cname, cnt in det_results["class_counts"].items():
                    all_class_counts[cname] = max(all_class_counts.get(cname, 0), cnt)

                # Render temporary annotated preview
                shelf_statuses_temp = {}
                for s in shelves:
                    sid = s["shelf_id"]
                    c = det_results["shelf_counts"].get(sid, 0)
                    shelf_statuses_temp[sid] = classify_stock_status(
                        detected_count=c,
                        expected_capacity=s["expected_capacity"],
                        low_stock_threshold=s["low_stock_threshold"],
                        empty_threshold=s["empty_threshold"]
                    )
                annotated = detector_instance.render_annotated_frame(
                    frame, det_results["detections"], shelves, shelf_statuses_temp
                )
                last_annotated_b64 = frame_to_base64(annotated)

            frame_idx += 1

        cap.release()

        if frames_processed == 0:
            raise HTTPException(status_code=400, detail="No readable frames could be sampled from video.")

        # Aggregate per-shelf stock status across sampled frames
        final_shelf_statuses = {}
        run = DetectionRun(
            input_type="video",
            source_reference=file.filename,
            model_version=detector_instance.model_name,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        for s in shelves:
            sid = s["shelf_id"]
            counts_list = shelf_counts_accum.get(sid, [0])
            avg_count = int(round(np.mean(counts_list))) if counts_list else 0

            status_info = classify_stock_status(
                detected_count=avg_count,
                expected_capacity=s["expected_capacity"],
                low_stock_threshold=s["low_stock_threshold"],
                empty_threshold=s["empty_threshold"]
            )
            final_shelf_statuses[sid] = status_info

            inv = Inventory(
                shelf_id=sid,
                run_id=run.run_id,
                detected_count=avg_count,
                occupancy_ratio=status_info["occupancy_ratio"],
                status=status_info["status"],
                recorded_at=datetime.utcnow()
            )
            db.add(inv)

            if status_info["status"] in [StockClassification.LOW_STOCK, StockClassification.EMPTY]:
                alert = Alert(
                    alert_type="LOW_STOCK" if status_info["status"] == StockClassification.LOW_STOCK else "EMPTY_SHELF",
                    shelf_id=sid,
                    message=f"Video Run Alert: Shelf '{s['name']}' averaged {status_info['status']} ({avg_count}/{s['expected_capacity']} items)",
                    severity=status_info["severity"],
                    is_resolved=False
                )
                db.add(alert)

        db.commit()
        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "run_id": run.run_id,
            "input_type": "video",
            "source_reference": file.filename,
            "frames_sampled": frames_processed,
            "total_frames": total_frames,
            "class_counts": all_class_counts,
            "shelf_statuses": final_shelf_statuses,
            "annotated_image_url": last_annotated_b64,
            "processing_time_ms": elapsed_ms
        }

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

