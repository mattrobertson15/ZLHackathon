import json

from sqlalchemy import Column, DateTime, String, Text

from app.db.database import Base


class Zone(Base):
    """A named physical area of a facility with a defined PPE policy.

    See ZONE_CAMERA_PLAN.md#1-shared-location-schema. required_ppe and
    severity_overrides are stored as JSON text to avoid a dedicated table for
    the hackathon; helpers parse them back into Python structures.
    """

    __tablename__ = "zones"

    id = Column(String, primary_key=True)  # slug, e.g. "loading-dock"
    display_name = Column(String, nullable=False)
    required_ppe = Column(Text, nullable=False, default="[]")  # JSON array
    severity_overrides = Column(Text, nullable=False, default="{}")  # JSON object
    created_at = Column(DateTime, nullable=False)

    def required_ppe_items(self) -> list[str]:
        try:
            return list(json.loads(self.required_ppe or "[]"))
        except (json.JSONDecodeError, TypeError):
            return []

    def severity_overrides_map(self) -> dict[str, str]:
        try:
            return dict(json.loads(self.severity_overrides or "{}"))
        except (json.JSONDecodeError, TypeError):
            return {}
