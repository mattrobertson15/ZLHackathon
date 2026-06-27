"""Shared pytest fixtures for Safety Sentinel backend tests.

Design notes
------------
* A throwaway temp directory holds both the SQLite DB and the upload storage so
  tests never touch the developer's real ``safety_sentinel.db`` or ``./uploads``.
  These env vars MUST be set before importing any ``app.*`` module, because
  ``app.config`` reads them at import time and ``app.db.database`` binds its
  engine to ``DATABASE_URL`` at import time.
* Real vision/LLM providers are disabled: ROBOFLOW/QWEN keys are cleared so
  ``modelProvider="auto"`` deterministically falls back to ``manual_mock``, and
  summary tests stub the Anthropic client (see ``fake_anthropic``).
* The ``client`` fixture uses ``TestClient(app)`` WITHOUT the ``with`` context
  manager on purpose: that skips FastAPI startup/shutdown events, so the
  background camera-monitor thread never starts during tests. Schema creation
  and seeding are done explicitly in ``db_session`` instead.
"""

import os
import pathlib
import tempfile

_TMP = tempfile.mkdtemp(prefix="ss-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["UPLOAD_STORAGE_PATH"] = str(pathlib.Path(_TMP) / "uploads")
os.makedirs(os.environ["UPLOAD_STORAGE_PATH"], exist_ok=True)
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
# Force deterministic mock inference regardless of the developer's real env.
os.environ.pop("ROBOFLOW_API_KEY", None)
os.environ.pop("QWEN_API_KEY", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, SessionLocal, engine, get_db, init_db  # noqa: E402
from app.db.seeds import seed_location_data  # noqa: E402
from app.main import app  # noqa: E402

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture
def db_session():
    """A fresh, seeded database session for one test.

    The schema is dropped and recreated each test so cases stay isolated, then
    seeded with the same zones/cameras the app seeds at startup.
    """
    Base.metadata.drop_all(bind=engine)
    init_db()
    session = SessionLocal()
    seed_location_data(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """A TestClient whose requests all share the seeded ``db_session``.

    Sharing one session means rows written through the API are immediately
    visible to in-test assertions that query ``db_session`` directly.
    """

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes():
    """Bytes of a real bundled worksite image, for upload tests."""
    return (_REPO_ROOT / "uploads" / "002823.jpg").read_bytes()


class _FakeMessage:
    def __init__(self, text):
        self.content = [type("Block", (), {"text": text})()]


class _FakeAnthropic:
    """Stand-in for ``anthropic.Anthropic`` returning a canned, parseable reply."""

    CANNED = (
        "Executive Summary\n"
        "Overall PPE compliance was strong this period.\n\n"
        "Top Violations\n"
        "Missing safety vests were the most common issue, followed by missing helmets.\n\n"
        "Trend Analysis\n"
        "Compliance improved compared with the previous period.\n\n"
        "Recommended Actions\n"
        "Reinforce vest requirements during pre-shift briefings.\n"
        "Review PPE signage near high-traffic zones.\n"
    )

    def __init__(self, *args, **kwargs):
        self.messages = self

    def create(self, *args, **kwargs):  # mirrors client.messages.create(...)
        return _FakeMessage(self.CANNED)


@pytest.fixture
def fake_anthropic(monkeypatch):
    """Patch the Anthropic client so summary tests never hit the network."""
    from app.services import summary_service

    monkeypatch.setattr(summary_service.anthropic, "Anthropic", _FakeAnthropic)
    return _FakeAnthropic
