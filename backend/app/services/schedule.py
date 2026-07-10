"""
Nightly scrape scheduler (R4.1).

Wraps an APScheduler AsyncIOScheduler that fires run_scrape_job on a
configurable cron schedule. The scheduler lives inside the single uvicorn
worker (INV-9 — the single-process assumption is not relaxed). The existing
in-memory scrape lock guards against overlap with manually-triggered scrapes
(design_decisions D4 — refuse, not queue). APScheduler's max_instances=1
additionally prevents the scheduler from stacking the job with itself if a
scheduled run overruns its slot.

Env vars:
  SCRAPE_SCHEDULE_ENABLED  "true" / "false"   (default "false" — opt-in)
  SCRAPE_SCHEDULE_CRON     crontab string      (default "0 3 * * *" = 3 am daily)

Timezone is fixed to America/Toronto (the runner's local zone); the cron
expression is interpreted in that zone regardless of the server's system TZ.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_TZ = pytz.timezone("America/Toronto")
_JOB_ID = "nightly_scrape"

# Module-level singleton — one scheduler per process (INV-9).
_scheduler: Optional[AsyncIOScheduler] = None


def _is_enabled() -> bool:
    return os.getenv("SCRAPE_SCHEDULE_ENABLED", "false").lower() == "true"


def _cron_expr() -> str:
    return os.getenv("SCRAPE_SCHEDULE_CRON", "0 3 * * *")


async def _run_scheduled_scrape() -> None:
    """
    Entry point fired by the scheduler.

    Tries to acquire the process-wide scrape lock (D4 — refuse not queue).
    If a manual or background scrape is already running, logs and skips — the
    next scheduled slot will try again. run_scrape_job's finally always
    releases the lock, so acquisition here and release there are balanced.
    """
    from app.scrape_runner import run_scrape_job
    from app.scrapers.lock import try_acquire_scrape_lock

    if not try_acquire_scrape_lock():
        logger.info("Scheduled scrape skipped — a scrape is already in progress")
        return
    logger.info("Scheduled scrape starting")
    await run_scrape_job(trigger="scheduled")


def start() -> None:
    """
    Create and start the AsyncIOScheduler.

    Called from the app lifespan on startup. If SCRAPE_SCHEDULE_ENABLED is
    not "true", the scheduler still starts (so get_status() works) but no
    job is registered — the only effect is a small amount of idle overhead.
    """
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone=_TZ)

    if _is_enabled():
        cron = _cron_expr()
        trigger = CronTrigger.from_crontab(cron, timezone=_TZ)
        _scheduler.add_job(
            _run_scheduled_scrape,
            trigger,
            id=_JOB_ID,
            coalesce=True,        # misfire → run once, not N times
            max_instances=1,      # never overlap two scheduled runs
            replace_existing=True,
        )
        logger.info(f"Scheduled scraping enabled: cron={cron!r} (America/Toronto)")
    else:
        logger.info("Scheduled scraping disabled (SCRAPE_SCHEDULE_ENABLED != true)")

    _scheduler.start()


def shutdown() -> None:
    """Stop the scheduler. Called from the app lifespan on teardown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _scheduler = None


def get_status() -> dict:
    """
    Current schedule state for the admin endpoint and the Settings UI.

    Returns:
        enabled          bool       — whether SCRAPE_SCHEDULE_ENABLED=true
        cron             str        — the configured cron expression
        next_run_utc     str|None   — ISO datetime of the next fire, or null
        scheduler_running bool      — whether the APScheduler instance is alive
    """
    enabled = _is_enabled()
    cron = _cron_expr()
    next_run: Optional[str] = None
    running = _scheduler is not None and _scheduler.running

    if running and enabled:
        job = _scheduler.get_job(_JOB_ID)
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()

    return {
        "enabled": enabled,
        "cron": cron,
        "next_run_utc": next_run,
        "scheduler_running": running,
    }
