from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # psycopg2 drops the project-ref suffix from usernames like
    # "postgres.project-ref" when parsing the URL, so pass it explicitly.
    _parsed = urlparse(DATABASE_URL)
    connect_args = {"user": _parsed.username} if _parsed.username else {}

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
        "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS zone_id VARCHAR",
        "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS camera_id VARCHAR",
        "ALTER TABLE detection_results ADD COLUMN IF NOT EXISTS frame_url TEXT",
        "ALTER TABLE safety_events ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP",
        "ALTER TABLE safety_events ADD COLUMN IF NOT EXISTS review_note TEXT",
    ]
    with engine.connect() as conn:
        for stmt in new_columns:
            conn.execute(text(stmt))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
