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
    _apply_migrations()


def _apply_migrations():
    """Add columns that may be missing from databases created before these fields existed."""
    from sqlalchemy import text

    new_columns = [
        "ALTER TABLE uploads ADD COLUMN zone_id VARCHAR",
        "ALTER TABLE uploads ADD COLUMN camera_id VARCHAR",
        "ALTER TABLE uploads ADD COLUMN source_type TEXT DEFAULT 'upload'",
        "ALTER TABLE detection_results ADD COLUMN frame_url TEXT",
        "ALTER TABLE safety_events ADD COLUMN status_updated_at DATETIME",
        "ALTER TABLE safety_events ADD COLUMN review_note TEXT",
        # Live RTSP feed columns on the (previously location-only) cameras table.
        "ALTER TABLE cameras ADD COLUMN rtsp_url VARCHAR",
        "ALTER TABLE cameras ADD COLUMN stream_status TEXT DEFAULT 'offline'",
        "ALTER TABLE cameras ADD COLUMN monitoring BOOLEAN DEFAULT 0",
        "ALTER TABLE cameras ADD COLUMN capture_interval_seconds INTEGER DEFAULT 15",
        "ALTER TABLE cameras ADD COLUMN last_capture_at DATETIME",
        "ALTER TABLE cameras ADD COLUMN last_error VARCHAR",
    ]
    with engine.connect() as conn:
        for stmt in new_columns:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass  # Column already exists


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
