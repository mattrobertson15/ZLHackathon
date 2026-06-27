from sqlalchemy import Column, DateTime, String

from app.db.database import Base


class Camera(Base):
    """A logical clip source pre-assigned to a zone.

    See ZONE_CAMERA_PLAN.md#1-shared-location-schema. Authenticated camera
    ingest and API-key issuance are intentionally out of scope for this pass;
    cameras exist so uploads can be assigned to a camera and inherit its zone.
    """

    __tablename__ = "cameras"

    id = Column(String, primary_key=True)  # slug, e.g. "cam-02"
    display_name = Column(String, nullable=False)
    zone_id = Column(String, nullable=False)  # FK -> zones.id
    status = Column(String, nullable=False, default="active")  # active | inactive
    created_at = Column(DateTime, nullable=False)
