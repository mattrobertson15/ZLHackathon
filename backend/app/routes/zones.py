import json
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
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


class CreateZoneRequest(BaseModel):
    displayName: str = Field(..., min_length=1, max_length=80)
    requiredPpe: list[str] = Field(default_factory=list)
    severityOverrides: dict[str, str] = Field(default_factory=dict)


@router.get("")
def get_zones(db: Session = Depends(get_db)):
    return {"zones": [serialize_zone(z) for z in list_zones(db)]}


@router.post("")
def create_zone(body: CreateZoneRequest, db: Session = Depends(get_db)):
    valid_ppe = {"helmet", "no_helmet", "vest", "no_vest"}
    valid_severity = {"low", "medium", "high"}

    bad_ppe = [p for p in body.requiredPpe if p not in valid_ppe]
    if bad_ppe:
        raise HTTPException(status_code=422, detail=_error("INVALID_PPE", f"Unknown PPE items: {bad_ppe}"))

    for k, v in body.severityOverrides.items():
        if v not in valid_severity:
            raise HTTPException(status_code=422, detail=_error("INVALID_SEVERITY", f"Unknown severity: {v}"))

    zone_id = re.sub(r"[^a-z0-9]+", "-", body.displayName.lower()).strip("-")
    if get_zone(db, zone_id):
        raise HTTPException(status_code=409, detail=_error("ZONE_EXISTS", f"Zone '{zone_id}' already exists."))

    zone = Zone(
        id=zone_id,
        display_name=body.displayName,
        required_ppe=json.dumps(body.requiredPpe),
        severity_overrides=json.dumps(body.severityOverrides),
        created_at=datetime.now(timezone.utc),
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return {"zone": serialize_zone(zone)}


@router.get("/{zone_id}")
def get_zone_by_id(zone_id: str, db: Session = Depends(get_db)):
    zone = get_zone(db, zone_id)
    if zone is None:
        raise HTTPException(
            status_code=404,
            detail=_error("ZONE_NOT_FOUND", f"No zone found for id '{zone_id}'."),
        )
    return {"zone": serialize_zone(zone)}
