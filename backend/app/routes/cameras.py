import os
import shutil
import tempfile

import cv2
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
    get_zone,
    list_cameras,
    list_events_for_camera,
    list_uploads_for_camera,
    update_camera,
)
from app.models.camera import Camera
from app.services import camera_monitor
from app.services.serializers import serialize_event, serialize_upload
from app.utils.ids import generate_id
from app.utils.rtsp_capture import capture_frames_from_rtsp
from app.utils.timestamps import now_utc, to_iso

router = APIRouter(prefix="/cameras", tags=["cameras"])


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


def serialize_camera(camera: Camera, recent_event_count: int = 0) -> dict:
    """Superset serializer: location-registry fields (main) + live-feed fields.

    Clients that only know the registry shape (displayName/zoneId/status) keep
    working; the RTSP feature reads the additional stream fields.
    """
    return {
        "id": camera.id,
        "displayName": camera.display_name,
        "zoneId": camera.zone_id,
        "status": camera.status,
        "createdAt": to_iso(camera.created_at),
        # Live RTSP feed
        "rtspUrl": camera.rtsp_url,
        "streamStatus": camera.stream_status,
        "monitoring": camera.monitoring,
        "captureIntervalSeconds": camera.capture_interval_seconds,
        "lastCaptureAt": to_iso(camera.last_capture_at) if camera.last_capture_at else None,
        "lastError": camera.last_error,
        "recentEventCount": recent_event_count,
    }


class CreateCameraRequest(BaseModel):
    displayName: str
    rtspUrl: str | None = None
    zoneId: str | None = None
    captureIntervalSeconds: int = 15


class TestStreamRequest(BaseModel):
    rtspUrl: str


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
    if request.captureIntervalSeconds < 1:
        raise HTTPException(
            status_code=400,
            detail=_error("INVALID_INTERVAL", "captureIntervalSeconds must be at least 1."),
        )
    if request.zoneId and get_zone(db, request.zoneId) is None:
        raise HTTPException(
            status_code=400,
            detail=_error("ZONE_NOT_FOUND", f"No zone found for id '{request.zoneId}'."),
        )

    camera = Camera(
        id=generate_id("cam"),
        display_name=request.displayName,
        zone_id=request.zoneId,
        status="active",
        created_at=now_utc(),
        rtsp_url=request.rtspUrl,
        stream_status="offline",
        monitoring=False,
        capture_interval_seconds=request.captureIntervalSeconds,
    )
    camera = create_camera(db, camera)
    return {"camera": _camera_payload(db, camera)}


@router.get("")
def get_cameras(db: Session = Depends(get_db)):
    return {"cameras": [_camera_payload(db, c) for c in list_cameras(db)]}


@router.post("/test-stream")
def test_stream(request: TestStreamRequest):
    """Probe an RTSP URL by grabbing a single frame, without registering a camera.

    Lets the user confirm the phone/relay feed is reachable before they start
    monitoring. Returns the frame dimensions on success, or a friendly failure
    message (the most common cause is the backend not being able to reach the
    stream). See API.md#test-rtsp-stream.
    """
    scratch_dir = tempfile.mkdtemp(prefix="test_stream_", dir=UPLOAD_STORAGE_PATH)
    try:
        captured = capture_frames_from_rtsp(
            request.rtspUrl, scratch_dir, num_frames=1, spacing_seconds=0
        )
        frame = cv2.imread(captured[0]["framePath"])
        if frame is None:
            raise ValueError("Captured frame could not be decoded.")
        height, width = frame.shape[:2]
        return {
            "status": "connected",
            "width": int(width),
            "height": int(height),
            "message": "Stream connected successfully.",
        }
    except Exception:
        return {
            "status": "failed",
            "message": (
                "Unable to read a frame from the RTSP stream. Make sure the stream "
                "is live and reachable from the backend (for a phone, push to the "
                "relay rather than exposing the phone's LAN address)."
            ),
        }
    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)


@router.get("/{camera_id}")
def get_camera_by_id(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    return {"camera": _camera_payload(db, camera)}


@router.get("/{camera_id}/detail")
def get_camera_detail(camera_id: str, db: Session = Depends(get_db)):
    """Camera plus its recent captures and events (for the camera UI)."""
    camera = _get_or_404(db, camera_id)
    uploads = list_uploads_for_camera(db, camera_id, limit=10)
    events = list_events_for_camera(db, camera_id, limit=20)
    return {
        "camera": _camera_payload(db, camera),
        "captures": [serialize_upload(u) for u in uploads],
        "events": [serialize_event(e) for e in events],
    }


def _require_rtsp(camera: Camera) -> None:
    if not camera.rtsp_url:
        raise HTTPException(
            status_code=400,
            detail=_error(
                "NO_RTSP_URL",
                f"Camera '{camera.id}' has no rtspUrl; it is a location-only camera.",
            ),
        )


@router.post("/{camera_id}/start")
def start_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    _require_rtsp(camera)
    camera.monitoring = True
    update_camera(db, camera)

    # Immediate capture so the user gets instant feedback and stream_status flips.
    try:
        camera_monitor.capture_and_analyze(db, camera)
    except Exception:
        # capture_and_analyze already recorded stream_status="error" + last_error.
        pass

    db.refresh(camera)
    return {"camera": _camera_payload(db, camera)}


@router.post("/{camera_id}/stop")
def stop_camera(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    camera.monitoring = False
    camera.stream_status = "offline"
    update_camera(db, camera)
    return {"camera": _camera_payload(db, camera)}


@router.post("/{camera_id}/capture")
def capture_now(camera_id: str, db: Session = Depends(get_db)):
    camera = _get_or_404(db, camera_id)
    _require_rtsp(camera)
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
    _get_or_404(db, camera_id)
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
