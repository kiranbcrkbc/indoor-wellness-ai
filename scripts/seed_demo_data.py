import os
import sys
import json
from datetime import datetime, timedelta

# Add workspace root to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, BASE_DIR)

from backend.app.db.database import engine, Base, SessionLocal
from backend.app.db.models import (
    Shelf, Product, DetectionRun, Detection, Inventory, Alert, SystemSetting, EnvironmentalReading, AQIPrediction
)


def seed_database():
    print("Seeding database with production demo data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Shelves
        if db.query(Shelf).count() == 0:
            s1 = Shelf(
                name="Shelf 1 - Top Rack (Beverages & Snacks)",
                roi_coordinates=json.dumps([[60, 70], [740, 210]]),
                expected_capacity=8,
                low_stock_threshold=0.35,
                empty_threshold=0.05
            )
            s2 = Shelf(
                name="Shelf 2 - Lower Rack (Packaged Goods)",
                roi_coordinates=json.dumps([[60, 280], [740, 430]]),
                expected_capacity=8,
                low_stock_threshold=0.35,
                empty_threshold=0.05
            )
            db.add_all([s1, s2])
            db.commit()
            print("  [+] Shelves seeded successfully.")

        s1 = db.query(Shelf).first()
        s2 = db.query(Shelf).offset(1).first()

        # 2. Seed Products
        products = ["bottle", "can", "cereal_box", "snack_bag", "cup", "carton"]
        for p in products:
            if not db.query(Product).filter(Product.name == p).first():
                db.add(Product(name=p, category="Retail Item"))
        db.commit()
        print("  [+] Product classes seeded.")

        p_bottle = db.query(Product).filter(Product.name == "bottle").first()

        # 3. Seed Historical Detection Runs & Inventory State
        if db.query(DetectionRun).count() == 0:
            now = datetime.utcnow()
            for i in range(5):
                t = now - timedelta(hours=(5 - i) * 2)
                run = DetectionRun(
                    input_type="demo",
                    source_reference=f"Demo Audit Session #{i+1}",
                    model_version="yolov8n",
                    started_at=t,
                    completed_at=t + timedelta(seconds=2)
                )
                db.add(run)
                db.commit()
                db.refresh(run)

                # Add sample detections
                det_count_s1 = 8 if i != 2 else 2
                det_count_s2 = 7 if i != 3 else 0

                for d in range(det_count_s1):
                    db.add(Detection(
                        run_id=run.run_id,
                        shelf_id=s1.shelf_id,
                        product_id=p_bottle.product_id,
                        confidence=0.88,
                        bbox_x=80 + d * 75,
                        bbox_y=95,
                        bbox_w=50,
                        bbox_h=100,
                        detected_at=t
                    ))

                # Inventory status for shelf 1
                status_s1 = "AVAILABLE" if det_count_s1 > 3 else ("LOW STOCK" if det_count_s1 > 0 else "EMPTY")
                db.add(Inventory(
                    shelf_id=s1.shelf_id,
                    run_id=run.run_id,
                    detected_count=det_count_s1,
                    occupancy_ratio=round(det_count_s1 / 8.0, 3),
                    status=status_s1,
                    recorded_at=t
                ))

                # Inventory status for shelf 2
                status_s2 = "AVAILABLE" if det_count_s2 > 3 else ("LOW STOCK" if det_count_s2 > 0 else "EMPTY")
                db.add(Inventory(
                    shelf_id=s2.shelf_id,
                    run_id=run.run_id,
                    detected_count=det_count_s2,
                    occupancy_ratio=round(det_count_s2 / 8.0, 3),
                    status=status_s2,
                    recorded_at=t
                ))

            print("  [+] Detection runs and inventory history seeded.")

        # 4. Seed Alerts
        if db.query(Alert).count() == 0:
            a1 = Alert(
                alert_type="LOW_STOCK",
                shelf_id=s1.shelf_id,
                message="Shelf 'Shelf 1 - Top Rack' transitioned to LOW STOCK (2/8 items remaining)",
                severity="WARNING",
                is_resolved=False,
                created_at=datetime.utcnow() - timedelta(minutes=45)
            )
            a2 = Alert(
                alert_type="HAZARDOUS_AQI",
                message="Indoor Air Alert: Transient VOC elevation detected (AQI 115, Moderate Circulation Active)",
                severity="WARNING",
                is_resolved=True,
                created_at=datetime.utcnow() - timedelta(hours=3),
                resolved_at=datetime.utcnow() - timedelta(hours=2)
            )
            db.add_all([a1, a2])
            db.commit()
            print("  [+] Alerts seeded.")

        # 5. Seed Environmental Baseline
        if db.query(EnvironmentalReading).count() == 0:
            reading = EnvironmentalReading(
                pm25=14.2,
                co2=530.0,
                voc=88.0,
                temperature=22.5,
                humidity=48.0,
                filtered_pm25=13.8,
                filtered_co2=528.0,
                predicted_aqi=28.5,
                air_quality_status="Good",
                ventilation_status="STANDBY",
                source="SOFTWARE SIMULATION",
                recorded_at=datetime.utcnow()
            )
            db.add(reading)
            db.commit()
            db.refresh(reading)

            db.add(AQIPrediction(
                reading_id=reading.reading_id,
                predicted_aqi=28.5,
                category="Good",
                primary_pollutant="PM2.5",
                forecast_1h=30.0,
                forecast_3h=32.0,
                forecast_6h=35.0,
                recommended_ventilation="STANDBY",
                actuator_power_level=10
            ))
            db.commit()
            print("  [+] Environmental telemetry baseline seeded.")

        # 6. Seed System Settings
        defaults = {
            "confidence_threshold": "0.45",
            "nms_iou_threshold": "0.45",
            "active_model_path": "models/pretrained/yolov8n.pt",
            "empty_threshold": "0.05",
            "low_stock_threshold": "0.35",
            "temporal_confirmation_frames": "3",
            "aqi_hazardous_threshold": "150.0",
            "simulation_scenario": "Normal Indoor"
        }
        for k, v in defaults.items():
            if not db.query(SystemSetting).filter(SystemSetting.setting_key == k).first():
                db.add(SystemSetting(setting_key=k, setting_value=v))
        db.commit()
        print("  [+] System settings seeded.")

        print("\nDatabase initialization complete! Ready for live demonstration.")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
