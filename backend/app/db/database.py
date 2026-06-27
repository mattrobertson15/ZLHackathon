from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    from app.models import (  # noqa: F401  (ensure models are registered)
        alert_record,
        camera,
        detection_result,
        safety_event,
        summary,
        upload,
        zone,
    )

    Base.metadata.create_all(bind=engine)
    _ensure_upload_columns()


def _ensure_upload_columns():
    """Additively add zone_id/camera_id to a pre-existing uploads table.

    create_all() creates new tables but never alters existing ones, so an older
    SQLite database would be missing the new nullable upload columns. These
    ALTERs are idempotent guards for that case; a fresh database already has them.
    """
    if not DATABASE_URL.startswith("sqlite"):
        return
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "uploads" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("uploads")}
    with engine.begin() as conn:
        if "zone_id" not in existing:
            conn.execute(text("ALTER TABLE uploads ADD COLUMN zone_id VARCHAR"))
        if "camera_id" not in existing:
            conn.execute(text("ALTER TABLE uploads ADD COLUMN camera_id VARCHAR"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
