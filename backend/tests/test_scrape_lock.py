"""
Tests for the scrape-lock wedge protection (M3 fix, 2026-07-07).

Covers the operational escape hatch (force-release), the tolerant release that
lets a defensive `finally` call release unconditionally, and the synchronous
status endpoints. The lock is a module-global threading.Lock, so each test
leaves it released via teardown.
"""
from app.routers.admin import release_scrape_lock_endpoint
from app.routers.scraping import scrape_status
from app.scrapers import lock


def teardown_function():
    # Never leave the process-wide lock held across tests.
    lock.force_release_scrape_lock()


def test_force_release_when_not_held_returns_was_held_false():
    assert lock.is_scrape_running() is False
    assert release_scrape_lock_endpoint() == {"was_held": False}


def test_force_release_when_held_releases_and_reports_true():
    assert lock.try_acquire_scrape_lock() is True
    assert lock.is_scrape_running() is True

    assert release_scrape_lock_endpoint() == {"was_held": True}
    assert lock.is_scrape_running() is False


def test_release_scrape_lock_tolerates_double_release():
    lock.try_acquire_scrape_lock()
    lock.release_scrape_lock()
    # A second, spurious release must not raise — a defensive finally can call
    # it even when the lock was already freed.
    lock.release_scrape_lock()
    assert lock.is_scrape_running() is False


def test_scrape_status_endpoint_reflects_lock():
    assert scrape_status() == {"scrape_running": False}
    lock.try_acquire_scrape_lock()
    assert scrape_status() == {"scrape_running": True}
