from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import Alert
from backend.app.schemas.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertOut])
def get_alerts(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, WARNING, CRITICAL"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Fetches system and shelf alerts in reverse chronological order."""
    query = db.query(Alert)
    if resolved is not None:
        query = query.filter(Alert.is_resolved == resolved)
    if severity:
        query = query.filter(Alert.severity == severity.upper())

    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts


@router.post("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Marks an active alert as resolved."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/resolve-all", status_code=status.HTTP_200_OK)
def resolve_all_alerts(db: Session = Depends(get_db)):
    """Marks all unresolved alerts as resolved."""
    now = datetime.utcnow()
    updated = db.query(Alert).filter(Alert.is_resolved == False).update({
        "is_resolved": True,
        "resolved_at": now
    })
    db.commit()
    return {"status": "success", "resolved_count": updated}
