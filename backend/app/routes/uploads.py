import os
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import UPLOAD_STORAGE_PATH
from app.db.database import get_db
from app.db.repositories import (
    create_upload,
    get_camera,
    get_upload,
    get_zone,
    list_alerts_for_upload,
    list_detection_results_for_upload,
    list_safety_events_for_upload,
    list_uploads,
)
from app.models.upload import Upload
from app.services.serializers import serialize_alert, serialize_detection, serialize_event
from app.utils.ids import generate_id
from app.utils.timestamps import now_utc, to_iso

router = APIRouter(prefix="/uploads", tags=["uploads"])

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


def _resolve_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    raise HTTPException(
        status_code=400,
        detail=_error(
            "INVALID_FILE_TYPE",
            f"Unsupported file extension '{ext}'. Allowed: images "
            f"({', '.join(sorted(IMAGE_EXTENSIONS))}) or videos "
            f"({', '.join(sorted(VIDEO_EXTENSIONS))}).",
        ),
    )


def _serialize_upload(upload: Upload, zone_display_name: str = None) -> dict:
    return {
        "id": upload.id,
        "fileName": upload.file_name,
        "fileType": upload.file_type,
        "fileUrl": upload.file_url,
        "locationLabel": upload.location_label,
        "zoneId": upload.zone_id,
        "cameraId": upload.camera_id,
        "zoneDisplayName": zone_display_name,
        "sourceType": getattr(upload, "source_type", None) or "upload",
        "notes": upload.notes,
        "uploadedAt": to_iso(upload.uploaded_at),
        "status": upload.status,
    }


def _zone_name(db: Session, zone_id: str) -> str:
    if not zone_id:
        return None
    zone = get_zone(db, zone_id)
    return zone.display_name if zone else None


@router.post("")
def upload_file(
    file: UploadFile = File(...),
    locationLabel: str = Form(None),
    zoneId: str = Form(None),
    cameraId: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db),
):
    file_type = _resolve_file_type(file.filename)

    # Resolve location: an assigned camera wins and supplies its zone; otherwise
    # use the zone picked directly. See ZONE_CAMERA_PLAN.md#5-backend-api-surface.
    resolved_zone_id = zoneId or None
    resolved_camera_id = None
    if cameraId:
        camera = get_camera(db, cameraId)
        if camera is None:
            raise HTTPException(
                status_code=400,
                detail=_error("CAMERA_NOT_FOUND", f"No camera found for id '{cameraId}'."),
            )
        resolved_camera_id = camera.id
        resolved_zone_id = camera.zone_id
    if resolved_zone_id and get_zone(db, resolved_zone_id) is None:
        raise HTTPException(
            status_code=400,
            detail=_error("ZONE_NOT_FOUND", f"No zone found for id '{resolved_zone_id}'."),
        )

    upload_id = generate_id("upl")
    ext = os.path.splitext(file.filename)[1].lower()
    stored_name = f"{upload_id}{ext}"

    stored_path = os.path.join(UPLOAD_STORAGE_PATH, stored_name)
    with open(stored_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)
    file_url = f"/media/{stored_name}"

    upload = Upload(
        id=upload_id,
        file_name=file.filename,
        file_type=file_type,
        file_url=file_url,
        location_label=locationLabel,
        zone_id=resolved_zone_id,
        camera_id=resolved_camera_id,
        notes=notes,
        status="uploaded",
        uploaded_at=now_utc(),
    )
    upload = create_upload(db, upload)

    return {"upload": _serialize_upload(upload, _zone_name(db, upload.zone_id))}


@router.get("")
def get_uploads(limit: int = None, db: Session = Depends(get_db)):
    uploads = list_uploads(db, limit=limit)
    zone_names = {
        u.zone_id: _zone_name(db, u.zone_id) for u in uploads if u.zone_id
    }
    return {
        "uploads": [
            _serialize_upload(u, zone_names.get(u.zone_id)) for u in uploads
        ]
    }


@router.get("/{upload_id}")
def get_upload_by_id(upload_id: str, db: Session = Depends(get_db)):
    upload = get_upload(db, upload_id)
    if upload is None:
        raise HTTPException(
            status_code=404,
            detail=_error("UPLOAD_NOT_FOUND", f"No upload found for id '{upload_id}'."),
        )
    return {"upload": _serialize_upload(upload, _zone_name(db, upload.zone_id))}


@router.get("/{upload_id}/results")
def get_upload_results(upload_id: str, db: Session = Depends(get_db)):
    """Read-only snapshot of the full upload -> detections -> events -> alerts chain.

    Unlike POST /uploads/{upload_id}/analyze, this never runs inference and is
    safe to call repeatedly (e.g. on page load/refresh).
    """
    upload = get_upload(db, upload_id)
    if upload is None:
        raise HTTPException(
            status_code=404,
            detail=_error("UPLOAD_NOT_FOUND", f"No upload found for id '{upload_id}'."),
        )

    detections = list_detection_results_for_upload(db, upload_id)
    events = list_safety_events_for_upload(db, upload_id)
    alerts = list_alerts_for_upload(db, upload_id)

    return {
        "upload": _serialize_upload(upload, _zone_name(db, upload.zone_id)),
        "detections": [serialize_detection(d) for d in detections],
        "events": [serialize_event(e) for e in events],
        "alerts": [serialize_alert(a) for a in alerts],
    }
