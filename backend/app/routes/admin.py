from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.alert_record import AlertRecord
from app.models.detection_result import DetectionResult
from app.models.safety_event import SafetyEvent

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reset")
def reset_incidents(db: Session = Depends(get_db)):
    """Reset all incidents by clearing SafetyEvents, AlertRecords, and DetectionResults."""
    try:
        db.query(DetectionResult).delete()
        db.query(AlertRecord).delete()
        db.query(SafetyEvent).delete()
        db.commit()
        return {"status": "success", "message": "All incidents reset successfully"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}, 500
