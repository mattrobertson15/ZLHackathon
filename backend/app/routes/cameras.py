from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import get_camera, list_cameras
from app.models.camera import Camera
from app.utils.timestamps import to_iso

router = APIRouter(prefix="/cameras", tags=["cameras"])


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


def serialize_camera(camera: Camera) -> dict:
    return {
        "id": camera.id,
        "displayName": camera.display_name,
        "zoneId": camera.zone_id,
        "status": camera.status,
        "createdAt": to_iso(camera.created_at),
    }


@router.get("")
def get_cameras(db: Session = Depends(get_db)):
    return {"cameras": [serialize_camera(c) for c in list_cameras(db)]}


@router.get("/{camera_id}")
def get_camera_by_id(camera_id: str, db: Session = Depends(get_db)):
    camera = get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(
            status_code=404,
            detail=_error("CAMERA_NOT_FOUND", f"No camera found for id '{camera_id}'."),
        )
    return {"camera": serialize_camera(camera)}
