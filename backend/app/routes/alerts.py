from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import get_alert, list_alerts, update_alert_status
from app.models.alert_record import AlertRecord
from app.utils.timestamps import to_iso

router = APIRouter(prefix="/alerts", tags=["alerts"])

VALID_STATUSES = {"draft", "queued", "sent_mock", "dismissed"}


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


def _serialize_alert(alert: AlertRecord) -> dict:
    return {
        "id": alert.id,
        "safetyEventId": alert.safety_event_id,
        "alertType": alert.alert_type,
        "title": alert.title,
        "message": alert.message,
        "status": alert.status,
        "createdAt": to_iso(alert.created_at),
    }


@router.get("")
def get_alerts(
    status: Optional[str] = None,
    alertType: Optional[str] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
):
    alerts = list_alerts(db, status=status, alert_type=alertType, limit=limit)
    return {"alerts": [_serialize_alert(a) for a in alerts]}


class UpdateAlertRequest(BaseModel):
    status: str


@router.patch("/{alert_id}")
def patch_alert(alert_id: str, request: UpdateAlertRequest, db: Session = Depends(get_db)):
    if request.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=_error(
                "INVALID_STATUS",
                f"Status must be one of {sorted(VALID_STATUSES)}.",
            ),
        )
    alert = update_alert_status(db, alert_id, request.status)
    if alert is None:
        raise HTTPException(
            status_code=404,
            detail=_error("ALERT_NOT_FOUND", f"No alert found for id '{alert_id}'."),
        )
    return {"alert": _serialize_alert(alert)}
