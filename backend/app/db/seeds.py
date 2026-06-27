"""Startup seed data for zones and demo cameras.

Seeds run only when the respective table is empty, so they are safe to call on
every startup. See ZONE_CAMERA_PLAN.md#7-sample-dataset.
"""

import json

from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.models.zone import Zone
from app.utils.timestamps import now_utc

# id -> (display_name, required_ppe, severity_overrides)
DEFAULT_ZONES = [
    ("general-floor", "General Floor", ["helmet"], {}),
    ("loading-dock", "Loading Dock", ["vest"], {"no_vest": "high"}),
    (
        "welding-station",
        "Welding Station",
        ["helmet", "vest"],
        {"no_helmet": "high", "no_vest": "high"},
    ),
    ("office-area", "Office / Admin", [], {}),
]

# id -> (display_name, zone_id)
DEMO_CAMERAS = [
    ("cam-01", "Floor Entry Cam", "general-floor"),
    ("cam-02", "Dock Camera North", "loading-dock"),
    ("cam-03", "Welding Bay Cam", "welding-station"),
]


def seed_default_zones(db: Session) -> int:
    """Insert the default zone policy set if the zones table is empty."""
    if db.query(Zone).count() > 0:
        return 0
    created_at = now_utc()
    zones = [
        Zone(
            id=zone_id,
            display_name=display_name,
            required_ppe=json.dumps(required_ppe),
            severity_overrides=json.dumps(severity_overrides),
            created_at=created_at,
        )
        for zone_id, display_name, required_ppe, severity_overrides in DEFAULT_ZONES
    ]
    db.add_all(zones)
    db.commit()
    return len(zones)


def seed_demo_cameras(db: Session) -> int:
    """Insert the demo cameras if the cameras table is empty."""
    if db.query(Camera).count() > 0:
        return 0
    created_at = now_utc()
    cameras = [
        Camera(
            id=camera_id,
            display_name=display_name,
            zone_id=zone_id,
            status="active",
            created_at=created_at,
        )
        for camera_id, display_name, zone_id in DEMO_CAMERAS
    ]
    db.add_all(cameras)
    db.commit()
    return len(cameras)


def seed_location_data(db: Session) -> dict:
    """Seed zones and cameras; returns counts of newly inserted rows."""
    return {
        "zones": seed_default_zones(db),
        "cameras": seed_demo_cameras(db),
    }
