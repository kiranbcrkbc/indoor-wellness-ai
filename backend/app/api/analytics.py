import io
import csv
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.database import get_db
from backend.app.db.models import DetectionRun, Detection, Inventory, Shelf, Alert, Product

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    """Computes aggregate analytics for dashboard charts and KPI summary widgets."""
    total_runs = db.query(func.count(DetectionRun.run_id)).scalar() or 0
    total_detections = db.query(func.count(Detection.detection_id)).scalar() or 0
    total_shelves = db.query(func.count(Shelf.shelf_id)).scalar() or 0

    # Low stock & empty counts across shelves
    low_stock_shelves = 0
    empty_shelves = 0
    available_shelves = 0

    shelves = db.query(Shelf).all()
    shelf_distribution = []

    for s in shelves:
        latest_inv = (
            db.query(Inventory)
            .filter(Inventory.shelf_id == s.shelf_id)
            .order_by(Inventory.recorded_at.desc())
            .first()
        )
        status = latest_inv.status if latest_inv else "AVAILABLE"
        count = latest_inv.detected_count if latest_inv else 0
        occupancy = latest_inv.occupancy_ratio if latest_inv else 0.0

        if status == "EMPTY":
            empty_shelves += 1
        elif status == "LOW STOCK":
            low_stock_shelves += 1
        else:
            available_shelves += 1

        shelf_distribution.append({
            "shelf_id": s.shelf_id,
            "name": s.name,
            "status": status,
            "count": count,
            "capacity": s.expected_capacity,
            "occupancy_pct": round(occupancy * 100, 1)
        })

    # Product category distribution
    class_counts_query = (
        db.query(Product.name, func.count(Detection.detection_id))
        .join(Detection, Detection.product_id == Product.product_id)
        .group_by(Product.name)
        .limit(8)
        .all()
    )
    product_distribution = {name: count for name, count in class_counts_query}

    # Alert severity counts
    active_alerts = db.query(func.count(Alert.alert_id)).filter(Alert.is_resolved == False).scalar() or 0
    critical_alerts = db.query(func.count(Alert.alert_id)).filter(Alert.severity == "CRITICAL", Alert.is_resolved == False).scalar() or 0

    return {
        "kpis": {
            "total_runs": total_runs,
            "total_detections": total_detections,
            "total_shelves": total_shelves,
            "available_shelves": available_shelves,
            "low_stock_shelves": low_stock_shelves,
            "empty_shelves": empty_shelves,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts
        },
        "shelf_distribution": shelf_distribution,
        "product_distribution": product_distribution
    }


@router.get("/export")
def export_audit_log_csv(db: Session = Depends(get_db)):
    """Exports detection and inventory audit log as downloadable CSV file."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Run ID", "Input Type", "Source", "Shelf Name",
        "Detected Count", "Capacity", "Occupancy Ratio", "Status", "Timestamp"
    ])

    records = (
        db.query(Inventory, Shelf, DetectionRun)
        .join(Shelf, Inventory.shelf_id == Shelf.shelf_id)
        .join(DetectionRun, Inventory.run_id == DetectionRun.run_id)
        .order_by(Inventory.recorded_at.desc())
        .limit(500)
        .all()
    )

    for inv, shelf, run in records:
        writer.writerow([
            run.run_id,
            run.input_type,
            run.source_reference,
            shelf.name,
            inv.detected_count,
            shelf.expected_capacity,
            inv.occupancy_ratio,
            inv.status,
            inv.recorded_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    csv_data = output.getvalue()
    filename = f"smart_shelf_audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
