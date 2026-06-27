from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.db.database import Base


class Camera(Base):
    """A registered (possibly emulated) CCTV camera identified by an RTSP URL.

    See ARCHITECTURE.md#camera--rtsp-ingestion-layer. Each monitoring cycle the
    background monitor captures frames from `rtsp_url` and runs them through the
    same inference pipeline used for file uploads, producing SafetyEvents.
    """

    __tablename__ = "cameras"

    id = Column(String, primary_key=True)
    label = Column(String, nullable=False)
    rtsp_url = Column(String, nullable=False)
    location_label = Column(String, nullable=True)
    status = Column(String, nullable=False, default="offline")
    # offline | live | error
    monitoring = Column(Boolean, nullable=False, default=False)
    capture_interval_seconds = Column(Integer, nullable=False, default=15)
    last_capture_at = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
