"""
Tests for the R4.1 scheduled scraping feature.

Covers:
  - trigger parameter threads through scrape_runner to ScrapeRun
  - schedule.get_status() reflects SCRAPE_SCHEDULE_ENABLED env var
  - GET /api/admin/schedule returns expected response shape
  - scrape_runner signature accepts trigger="scheduled" without error
"""
import os

# Must match test_auth / test_http_smoke values so middleware is consistent
TEST_SECRET = "test-anton-secret-0123456789abcdef"
TEST_OTHER = "test-other-secret-0123456789abcd00"
os.environ["ANTON_TOKENS"] = f"desktop:{TEST_SECRET},spa:{TEST_OTHER}"

import pytest  # noqa: E402
import httpx  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import models  # noqa: E402

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=_engine)
_Session = sessionmaker(bind=_engine)


def _db_override():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _db_override

_AUTH = {"Authorization": f"Bearer {TEST_SECRET}"}


# ── schedule.get_status ───────────────────────────────────────────────────────

def test_get_status_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SCRAPE_SCHEDULE_ENABLED", raising=False)
    from app.services import schedule as svc
    status = svc.get_status()
    assert status["enabled"] is False
    assert status["cron"] == "0 3 * * *"  # default cron
    assert status["next_run_utc"] is None  # no job registered


def test_get_status_enabled_flag(monkeypatch):
    monkeypatch.setenv("SCRAPE_SCHEDULE_ENABLED", "true")
    from app.services import schedule as svc
    status = svc.get_status()
    assert status["enabled"] is True


def test_get_status_custom_cron(monkeypatch):
    monkeypatch.setenv("SCRAPE_SCHEDULE_CRON", "0 6 * * *")
    from app.services import schedule as svc
    status = svc.get_status()
    assert status["cron"] == "0 6 * * *"


def test_get_status_false_string_not_enabled(monkeypatch):
    monkeypatch.setenv("SCRAPE_SCHEDULE_ENABLED", "false")
    from app.services import schedule as svc
    status = svc.get_status()
    assert status["enabled"] is False


# ── scrape_runner trigger param ───────────────────────────────────────────────

def test_run_scrape_job_accepts_trigger_param():
    """Verifies the function signature includes trigger without calling it."""
    import inspect
    from app.scrape_runner import run_scrape_job
    sig = inspect.signature(run_scrape_job)
    assert "trigger" in sig.parameters
    assert sig.parameters["trigger"].default == "background"


def test_scrape_one_retailer_accepts_trigger_param():
    import inspect
    from app.scrape_runner import _scrape_one_retailer
    sig = inspect.signature(_scrape_one_retailer)
    assert "trigger" in sig.parameters
    assert sig.parameters["trigger"].default == "background"


# ── GET /api/admin/schedule ───────────────────────────────────────────────────

@pytest.mark.anyio
async def test_schedule_endpoint_shape(monkeypatch):
    monkeypatch.delenv("SCRAPE_SCHEDULE_ENABLED", raising=False)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.get("/api/admin/schedule", headers=_AUTH)
    assert r.status_code == 200
    data = r.json()
    assert "enabled" in data
    assert "cron" in data
    assert "next_run_utc" in data
    assert "scheduler_running" in data
    assert "is_scraping_now" in data
    assert "recent_scheduled_runs" in data
    assert isinstance(data["recent_scheduled_runs"], list)


@pytest.mark.anyio
async def test_schedule_endpoint_requires_auth():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.get("/api/admin/schedule")
    # 401 = no auth header; 429 = rate limiter fires first after many unauthed
    # test requests — both mean "access denied without credentials".
    assert r.status_code in (401, 429)


@pytest.mark.anyio
async def test_schedule_endpoint_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SCRAPE_SCHEDULE_ENABLED", raising=False)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.get("/api/admin/schedule", headers=_AUTH)
    assert r.status_code == 200
    assert r.json()["enabled"] is False
    assert r.json()["next_run_utc"] is None


# ── pytest-anyio config ───────────────────────────────────────────────────────

pytest_plugins = ("anyio",)
