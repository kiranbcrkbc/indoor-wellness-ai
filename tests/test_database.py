import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.database import Base
from backend.app.db.models import Shelf, Product, DetectionRun, Detection, Inventory, Alert


def test_database_crud_operations():
    # Use in-memory SQLite database for fast isolated unit test
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()

    try:
        # 1. Insert Shelf
        shelf = Shelf(
            name="Test Shelf 1",
            roi_coordinates=json.dumps([[10, 10], [200, 200]]),
            expected_capacity=10,
            low_stock_threshold=0.3,
            empty_threshold=0.05
        )
        db.add(shelf)
        db.commit()
        db.refresh(shelf)
        assert shelf.shelf_id is not None
        assert shelf.name == "Test Shelf 1"

        # 2. Insert Product
        product = Product(name="bottle", category="Beverage")
        db.add(product)
        db.commit()
        db.refresh(product)
        assert product.product_id is not None

        # 3. Insert Run & Detection
        run = DetectionRun(input_type="test", source_reference="unit_test")
        db.add(run)
        db.commit()
        db.refresh(run)

        det = Detection(
            run_id=run.run_id,
            shelf_id=shelf.shelf_id,
            product_id=product.product_id,
            confidence=0.92,
            bbox_x=50.0,
            bbox_y=60.0,
            bbox_w=40.0,
            bbox_h=80.0
        )
        db.add(det)
        db.commit()
        db.refresh(det)
        assert det.detection_id is not None

        # 4. Insert Inventory
        inv = Inventory(
            shelf_id=shelf.shelf_id,
            run_id=run.run_id,
            detected_count=1,
            occupancy_ratio=0.1,
            status="LOW STOCK"
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        assert inv.status == "LOW STOCK"

        # 5. Insert and Resolve Alert
        alert = Alert(
            alert_type="LOW_STOCK",
            shelf_id=shelf.shelf_id,
            message="Test alert: Low Stock",
            severity="WARNING",
            is_resolved=False
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        assert alert.is_resolved is False

        # Resolve
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)
        assert alert.is_resolved is True
        assert alert.resolved_at is not None

    finally:
        db.close()
