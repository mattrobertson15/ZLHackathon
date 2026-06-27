from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.db.database import Base


class Camera(Base):
    """A logical clip source pre-assigned to a zone, optionally a live RTSP feed.

    Unifies two ideas (see ZONE_CAMERA_PLAN.md#1-shared-location-schema and
    ARCHITECTURE.md#12-camera--rtsp-ingestion-layer):

    * Location registry — every camera belongs to a `zone_id`, so uploads (and
      live captures) assigned to it inherit the zone's PPE policy.
    * Optional RTSP feed — when `rtsp_url` is set the background monitor can
      continuously capture frames from the camera and raise events. Cameras
      without an `rtsp_url` are pure location records (e.g. the seeded demo
      cameras).

    `status` is the registry state (active | inactive). `stream_status` tracks
    live-feed connectivity (offline | live | error) and only matters when the
    camera is being monitored.
    """

    __tablename__ = "cameras"

    id = Column(String, primary_key=True)  # slug (e.g. "cam-02") or generated id
    display_name = Column(String, nullable=False)
    zone_id = Column(String, nullable=True)  # FK -> zones.id
    status = Column(String, nullable=False, default="active")  # active | inactive
    created_at = Column(DateTime, nullable=False)

    # --- Live RTSP feed (optional) ---
    rtsp_url = Column(String, nullable=True)
    stream_status = Column(String, nullable=False, default="offline")
    # offline | live | error
    monitoring = Column(Boolean, nullable=False, default=False)
    capture_interval_seconds = Column(Integer, nullable=False, default=15)
    last_capture_at = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)
