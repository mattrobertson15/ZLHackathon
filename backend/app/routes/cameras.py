import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import UPLOAD_STORAGE_PATH
from app.db.database import get_db
from app.db.repositories import (
    count_events_for_camera,
    create_camera,
    delete_camera,
    get_camera,
    list_cameras,
    list_events_for_camera,
    list_uploads_for_camera,
    update_camera,
)
from app.models.camera import Camera
from app.services import camera_monitor
from app.services.serializers import serialize_camera, serialize_event, serialize_upload
from app.utils.ids import generate_id
from app.utils.timestamps import now_utc

router = APIRouter(prefix="/cameras", tags=["cameras"])


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


class CreateCameraRequest(BaseModel):
    label: str
    rtspUrl: str
    locationLabel: str | None = None
    captureIntervalSeconds: int = 15


def _camera_payload(db: Session, camera: Camera) -> dict:
    return serialize_camera(camera, recent_event_count=count_events_for_camera(db, camera.id))


def _get_or_404(db: Session, camera_id: str) -> Camera:
    camera = get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(
            status_code=404,
            detail=_error("CAMERA_NOT_FOUND", f"No camera found for id '{camera_id}'."),
        )
    return camera


@router.post("")
def register_camera(request: CreateCameraRequest, db: Session = Depends(get_db)):
    if request.captureIntervalSeconds < 5:
        raise HTTPException(
            status_code=400,
            detail=_error(
                "INVALID_INTERVAL", "captureIntervalSeconds must be at least 5."
            ),
        )

    camera = Camera(
        id=generate_id("cam"),
        label=request.label,
        rtsp_url=request.rtspUrl,
        location_label=request.locationLabel,
        status="offline",
        monitoring=False,
        capture_interval_seconds=request.captureIntervalSeconds,
        created_at=now_utc(),
    )
    camera = create_camera(db, camera)
    return {"camera": _camera_payload(db, camera)}


@router.get("")
def get_cameras(db: Session = Depends(get_db)):
    cameras = list_cameras(db)
    return {"cameras": [_camera_payload(db, c) for c in cameras]}


@router.get("/{camera_id}")
def get_camera_detail(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    uploads = list_uploads_for_camera(db, camera_id, limit=10)
    events = list_events_for_camera(db, camera_id, limit=20)
    return {
        "camera": _camera_payload(db, camera),
        "captures": [serialize_upload(u) for u in uploads],
        "events": [serialize_event(e) for e in events],
    }


@router.post("/{camera_id}/start")
def start_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    camera.monitoring = True
    update_camera(db, camera)

    # Do one immediate capture so the user gets instant feedback and the
    # status flips to live/error without waiting a full interval.
    try:
        camera_monitor.capture_and_analyze(db, camera)
    except Exception:
        # capture_and_analyze already recorded status="error" + last_error.
        pass

    db.refresh(camera)
    return {"camera": _camera_payload(db, camera)}


@router.post("/{camera_id}/stop")
def stop_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    camera.monitoring = False
    camera.status = "offline"
    update_camera(db, camera)
    return {"camera": _camera_payload(db, camera)}


@router.post("/{camera_id}/capture")
def capture_now(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    try:
        result = camera_monitor.capture_and_analyze(db, camera)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=_error("CAPTURE_FAILED", f"Could not capture from camera: {exc}"),
        ) from exc

    db.refresh(camera)
    return {
        "camera": _camera_payload(db, camera),
        "detections": len(result["detections"]),
        "events": [serialize_event(e) for e in result["events"]],
    }


@router.get("/{camera_id}/snapshot")
def camera_snapshot(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    uploads = list_uploads_for_camera(db, camera_id, limit=1)
    if not uploads or not uploads[0].file_url:
        raise HTTPException(
            status_code=404,
            detail=_error("NO_SNAPSHOT", "No capture available for this camera yet."),
        )

    stored_name = uploads[0].file_url.removeprefix("/media/")
    disk_path = os.path.join(UPLOAD_STORAGE_PATH, stored_name)
    if not os.path.exists(disk_path):
        raise HTTPException(
            status_code=404,
            detail=_error("NO_SNAPSHOT", "Snapshot frame is no longer on disk."),
        )
    return FileResponse(disk_path, media_type="image/jpeg")


@router.delete("/{camera_id}")
def remove_camera(camera_id: str, db: Session = Depends(get_db)):
    _get_or_404(db, camera_id)
    delete_camera(db, camera_id)
    return {"status": "success", "message": f"Camera '{camera_id}' removed."}
