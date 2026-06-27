from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories import get_zone, list_zones
from app.models.zone import Zone
from app.utils.timestamps import to_iso

router = APIRouter(prefix="/zones", tags=["zones"])


def _error(code: str, message: str):
    return {"error": {"code": code, "message": message}}


def serialize_zone(zone: Zone) -> dict:
    return {
        "id": zone.id,
        "displayName": zone.display_name,
        "requiredPpe": zone.required_ppe_items(),
        "severityOverrides": zone.severity_overrides_map(),
        "createdAt": to_iso(zone.created_at),
    }


@router.get("")
def get_zones(db: Session = Depends(get_db)):
    return {"zones": [serialize_zone(z) for z in list_zones(db)]}


@router.get("/{zone_id}")
def get_zone_by_id(zone_id: str, db: Session = Depends(get_db)):
    zone = get_zone(db, zone_id)
    if zone is None:
        raise HTTPException(
            status_code=404,
            detail=_error("ZONE_NOT_FOUND", f"No zone found for id '{zone_id}'."),
        )
    return {"zone": serialize_zone(zone)}
