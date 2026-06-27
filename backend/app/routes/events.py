from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import get_safety_event, get_upload, list_safety_events, update_safety_event_status
from app.models.safety_event import SafetyEvent
from app.models.upload import Upload
from app.utils.timestamps import to_iso

router = APIRouter(prefix="/events", tags=["events"])

VALID_STATUSES = {"open", "reviewed", "dismissed", "resolved"}


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


def _serialize_upload(upload: Optional[Upload]) -> Optional[dict]:
    if upload is None:
        return None
    return {
        "id": upload.id,
        "fileName": upload.file_name,
        "fileType": upload.file_type,
        "fileUrl": upload.file_url,
        "locationLabel": upload.location_label,
        "notes": upload.notes,
        "uploadedAt": to_iso(upload.uploaded_at),
        "status": upload.status,
    }


def _serialize_event(event: SafetyEvent, upload: Optional[Upload] = None) -> dict:
    payload = {
        "id": event.id,
        "uploadId": event.upload_id,
        "eventType": event.event_type,
        "violationType": event.violation_type,
        "severity": event.severity,
        "confidence": event.confidence,
        "status": event.status,
        "suggestedAction": event.suggested_action,
        "createdAt": to_iso(event.created_at),
    }
    if upload is not None:
        payload["upload"] = _serialize_upload(upload)
    return payload


@router.get("")
def get_events(
    status: Optional[str] = None,
    eventType: Optional[str] = None,
    violationType: Optional[str] = None,
    severity: Optional[str] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
):
    events = list_safety_events(
        db,
        status=status,
        event_type=eventType,
        violation_type=violationType,
        severity=severity,
        limit=limit,
    )
    uploads = {
        upload_id: get_upload(db, upload_id)
        for upload_id in {e.upload_id for e in events}
    }
    return {"events": [_serialize_event(e, uploads.get(e.upload_id)) for e in events]}


@router.get("/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = get_safety_event(db, event_id)
    if event is None:
        raise HTTPException(
            status_code=404,
            detail=_error("EVENT_NOT_FOUND", f"No safety event found for id '{event_id}'."),
        )
    return {"event": _serialize_event(event, get_upload(db, event.upload_id))}


class UpdateEventRequest(BaseModel):
    status: str


@router.patch("/{event_id}")
def patch_event(event_id: str, request: UpdateEventRequest, db: Session = Depends(get_db)):
    if request.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=_error(
                "INVALID_STATUS",
                f"Status must be one of {sorted(VALID_STATUSES)}.",
            ),
        )
    event = update_safety_event_status(db, event_id, request.status)
    if event is None:
        raise HTTPException(
            status_code=404,
            detail=_error("EVENT_NOT_FOUND", f"No safety event found for id '{event_id}'."),
        )
    return {"event": _serialize_event(event, get_upload(db, event.upload_id))}
