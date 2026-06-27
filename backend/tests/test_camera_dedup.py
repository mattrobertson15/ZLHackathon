"""Live-capture deduplication tests for the camera repository helpers.

Covers the two queries the camera monitor relies on to avoid spawning a new
event/alert for the same person every capture cycle:
``find_recent_open_violation_for_camera`` and ``delete_safety_events_with_alerts``.
See ARCHITECTURE.md#camera--rtsp-ingestion-layer.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.repositories import (
    delete_safety_events_with_alerts,
    find_recent_open_violation_for_camera,
)
from app.models.alert_record import AlertRecord
from app.models.camera import Camera
from app.models.safety_event import SafetyEvent
from app.models.upload import Upload

_NOW = datetime.now(timezone.utc)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _seed_camera(db, camera_id="cam-x"):
    db.add(Camera(id=camera_id, display_name="Cam X", status="active", created_at=_NOW))
    db.commit()
    return camera_id


def _add_capture(db, camera_id, upload_id, violation_type, secs_ago=0, status="open"):
    db.add(
        Upload(
            id=upload_id,
            file_name="cap.jpg",
            file_type="video",
            file_url=f"/media/{upload_id}.jpg",
            camera_id=camera_id,
            source_type="camera",
            status="processed",
            uploaded_at=_NOW,
        )
    )
    event = SafetyEvent(
        id=f"evt-{upload_id}",
        upload_id=upload_id,
        event_type="ppe_violation",
        violation_type=violation_type,
        severity="high",
        confidence=0.9,
        status=status,
        suggested_action="x",
        created_at=_NOW - timedelta(seconds=secs_ago),
    )
    db.add(event)
    db.commit()
    return event


def test_recent_open_violation_found_within_window(db):
    cam = _seed_camera(db)
    _add_capture(db, cam, "u-prev", "no_helmet", secs_ago=10)
    found = find_recent_open_violation_for_camera(db, cam, "no_helmet", 30)
    assert found is not None
    assert found.upload_id == "u-prev"


def test_outside_window_not_found(db):
    cam = _seed_camera(db)
    _add_capture(db, cam, "u-old", "no_helmet", secs_ago=45)
    assert find_recent_open_violation_for_camera(db, cam, "no_helmet", 30) is None


def test_excludes_current_upload(db):
    cam = _seed_camera(db)
    _add_capture(db, cam, "u-now", "no_helmet", secs_ago=0)
    # The only matching event belongs to the current capture -> treated as no prior.
    assert (
        find_recent_open_violation_for_camera(
            db, cam, "no_helmet", 30, exclude_upload_id="u-now"
        )
        is None
    )


def test_different_violation_type_not_matched(db):
    cam = _seed_camera(db)
    _add_capture(db, cam, "u-vest", "no_vest", secs_ago=5)
    assert find_recent_open_violation_for_camera(db, cam, "no_helmet", 30) is None


def test_resolved_event_not_matched(db):
    cam = _seed_camera(db)
    _add_capture(db, cam, "u-done", "no_helmet", secs_ago=5, status="resolved")
    assert find_recent_open_violation_for_camera(db, cam, "no_helmet", 30) is None


def test_other_camera_not_matched(db):
    _seed_camera(db, "cam-a")
    _seed_camera(db, "cam-b")
    _add_capture(db, "cam-a", "u-a", "no_helmet", secs_ago=5)
    assert find_recent_open_violation_for_camera(db, "cam-b", "no_helmet", 30) is None


def test_delete_events_removes_linked_alerts(db):
    cam = _seed_camera(db)
    event = _add_capture(db, cam, "u-dup", "no_helmet", secs_ago=0)
    db.add(
        AlertRecord(
            id="alrt-1",
            safety_event_id=event.id,
            alert_type="supervisor_review",
            title="t",
            message="m",
            status="sent_mock",
            created_at=_NOW,
        )
    )
    db.commit()

    deleted = delete_safety_events_with_alerts(db, [event.id])
    assert deleted == 1
    assert db.query(SafetyEvent).count() == 0
    assert db.query(AlertRecord).count() == 0


def test_delete_empty_list_is_noop(db):
    assert delete_safety_events_with_alerts(db, []) == 0
