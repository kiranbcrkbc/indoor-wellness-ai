import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import Shelf, Inventory
from backend.app.schemas.schemas import ShelfCreate, ShelfUpdate, ShelfOut

router = APIRouter(prefix="/shelves", tags=["Shelves"])


@router.get("", response_model=List[ShelfOut])
def list_shelves(db: Session = Depends(get_db)):
    """Lists all configured shelf regions with latest occupancy and status."""
    shelves = db.query(Shelf).all()
    results = []
    for s in shelves:
        # Fetch latest inventory record if available
        latest_inv = (
            db.query(Inventory)
            .filter(Inventory.shelf_id == s.shelf_id)
            .order_by(Inventory.recorded_at.desc())
            .first()
        )
        roi_data = []
        if s.roi_coordinates:
            try:
                roi_data = json.loads(s.roi_coordinates)
            except Exception:
                roi_data = []

        results.append(
            ShelfOut(
                shelf_id=s.shelf_id,
                name=s.name,
                roi_coordinates=roi_data,
                expected_capacity=s.expected_capacity,
                low_stock_threshold=s.low_stock_threshold,
                empty_threshold=s.empty_threshold,
                created_at=s.created_at,
                current_count=latest_inv.detected_count if latest_inv else 0,
                current_occupancy=latest_inv.occupancy_ratio if latest_inv else 0.0,
                current_status=latest_inv.status if latest_inv else "AVAILABLE"
            )
        )
    return results


@router.post("", response_model=ShelfOut, status_code=status.HTTP_201_CREATED)
def create_shelf(payload: ShelfCreate, db: Session = Depends(get_db)):
    """Creates a new shelf ROI configuration."""
    shelf = Shelf(
        name=payload.name,
        roi_coordinates=json.dumps(payload.roi_coordinates),
        expected_capacity=payload.expected_capacity,
        low_stock_threshold=payload.low_stock_threshold,
        empty_threshold=payload.empty_threshold
    )
    db.add(shelf)
    db.commit()
    db.refresh(shelf)

    return ShelfOut(
        shelf_id=shelf.shelf_id,
        name=shelf.name,
        roi_coordinates=payload.roi_coordinates,
        expected_capacity=shelf.expected_capacity,
        low_stock_threshold=shelf.low_stock_threshold,
        empty_threshold=shelf.empty_threshold,
        created_at=shelf.created_at,
        current_count=0,
        current_occupancy=0.0,
        current_status="AVAILABLE"
    )


@router.put("/{shelf_id}", response_model=ShelfOut)
def update_shelf(shelf_id: int, payload: ShelfUpdate, db: Session = Depends(get_db)):
    """Updates an existing shelf configuration."""
    shelf = db.query(Shelf).filter(Shelf.shelf_id == shelf_id).first()
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    if payload.name is not None:
        shelf.name = payload.name
    if payload.roi_coordinates is not None:
        shelf.roi_coordinates = json.dumps(payload.roi_coordinates)
    if payload.expected_capacity is not None:
        shelf.expected_capacity = payload.expected_capacity
    if payload.low_stock_threshold is not None:
        shelf.low_stock_threshold = payload.low_stock_threshold
    if payload.empty_threshold is not None:
        shelf.empty_threshold = payload.empty_threshold

    db.commit()
    db.refresh(shelf)

    latest_inv = (
        db.query(Inventory)
        .filter(Inventory.shelf_id == shelf.shelf_id)
        .order_by(Inventory.recorded_at.desc())
        .first()
    )
    roi_data = []
    try:
        roi_data = json.loads(shelf.roi_coordinates)
    except Exception:
        roi_data = []

    return ShelfOut(
        shelf_id=shelf.shelf_id,
        name=shelf.name,
        roi_coordinates=roi_data,
        expected_capacity=shelf.expected_capacity,
        low_stock_threshold=shelf.low_stock_threshold,
        empty_threshold=shelf.empty_threshold,
        created_at=shelf.created_at,
        current_count=latest_inv.detected_count if latest_inv else 0,
        current_occupancy=latest_inv.occupancy_ratio if latest_inv else 0.0,
        current_status=latest_inv.status if latest_inv else "AVAILABLE"
    )


@router.delete("/{shelf_id}", status_code=status.HTTP_200_OK)
def delete_shelf(shelf_id: int, db: Session = Depends(get_db)):
    """Removes a shelf configuration."""
    shelf = db.query(Shelf).filter(Shelf.shelf_id == shelf_id).first()
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    db.delete(shelf)
    db.commit()
    return {"status": "success", "message": f"Shelf {shelf_id} deleted"}
