"""
API routes for COROS GPS watch sync.

Flow:
  1. GET  /status   — check credentials + last-sync time
  2. POST /fetch    — pull recent COROS runs, filter out already-logged ones
  3. POST /confirm  — accept user-assigned runs and log them to shoes

The user must explicitly confirm each assignment before any run is written
to the database. Nothing is auto-logged.
"""
from datetime import date as date_type, datetime, timezone
from typing import List, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.coros_client import (
    activity_to_run_dict,
    fetch_running_activities,
    get_coros_config,
)
from app.database import get_db
from app.models.models import AppSettings, OwnedShoe, ShoeRun
from app.models.schemas import (
    CorosAssignment,
    CorosConfirmRequest,
    CorosConfirmResponse,
    CorosFetchResponse,
    CorosRun,
    CorosSyncStatus,
    OwnedShoeResponse,
)
from app.routers.owned_shoes import CHECKPOINT_INTERVAL_KM, _attach_computed_fields

router = APIRouter(prefix="/owned-shoes/sync-coros", tags=["coros-sync"])


def _get_setting(db: Session, key: str) -> Optional[str]:
    row = db.query(AppSettings).filter(AppSettings.key == key).first()
    return row.value if row else None


def _set_setting(db: Session, key: str, value: str) -> None:
    row = db.query(AppSettings).filter(AppSettings.key == key).first()
    if row:
        row.value = value
    else:
        db.add(AppSettings(key=key, value=value))
    db.commit()


def _is_already_logged(db: Session, activity_id: str, act_date: str, dist_km: float) -> bool:
    """
    Two-tier dedup:
    1. Exact coros_activity_id match (primary — used after first sync).
    2. Same date + distance within 0.1km (secondary — catches runs logged
       manually before this feature existed).
    """
    if activity_id and db.query(ShoeRun).filter(
        ShoeRun.coros_activity_id == activity_id
    ).count():
        return True
    return db.query(ShoeRun).filter(
        ShoeRun.run_date == act_date,
        ShoeRun.distance_km.between(dist_km - 0.1, dist_km + 0.1),
    ).count() > 0


@router.get("/status", response_model=CorosSyncStatus)
def get_sync_status(db: Session = Depends(get_db)):
    """Return whether COROS credentials are configured and when we last synced."""
    config = get_coros_config()
    last_sync_str = _get_setting(db, "last_coros_sync_at")
    last_sync_at = datetime.fromisoformat(last_sync_str) if last_sync_str else None
    return CorosSyncStatus(
        coros_configured=config is not None,
        last_sync_at=last_sync_at,
        pending_runs=0,
    )


@router.post("/fetch", response_model=CorosFetchResponse)
def fetch_coros_runs(days_back: int = 30, db: Session = Depends(get_db)):
    """
    Fetch recent runs from COROS and return those not yet logged.

    Query param `days_back` controls the lookback window (default 30 days).
    Returns an empty list (not an error) when COROS is not configured.
    """
    config = get_coros_config()
    if not config:
        return CorosFetchResponse(runs=[], already_synced=0, coros_configured=False)

    try:
        activities = fetch_running_activities(config, days_back)
    except requests.exceptions.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"COROS API unreachable: {exc}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    new_runs: List[CorosRun] = []
    already_synced = 0

    for act in activities:
        run = activity_to_run_dict(act)
        if _is_already_logged(db, run["coros_activity_id"], run["date"], run["distance_km"]):
            already_synced += 1
        else:
            new_runs.append(CorosRun(**run))

    new_runs.sort(key=lambda r: r.date, reverse=True)

    return CorosFetchResponse(
        runs=new_runs,
        already_synced=already_synced,
        coros_configured=True,
    )


@router.post("/confirm", response_model=CorosConfirmResponse)
def confirm_coros_runs(body: CorosConfirmRequest, db: Session = Depends(get_db)):
    """
    Log user-confirmed COROS run → shoe assignments.

    Each assignment is written as a ShoeRun with source='coros'. Idempotent
    — double-submitting the same coros_activity_id is a no-op.
    """
    logged = 0
    updated_shoe_ids: set = set()

    for assignment in body.assignments:
        shoe = db.query(OwnedShoe).filter(OwnedShoe.id == assignment.owned_shoe_id).first()
        if not shoe:
            continue

        if db.query(ShoeRun).filter(
            ShoeRun.coros_activity_id == assignment.coros_activity_id
        ).count():
            continue

        run_date = date_type.fromisoformat(assignment.date)
        db_run = ShoeRun(
            owned_shoe_id=assignment.owned_shoe_id,
            distance_km=assignment.distance_km,
            run_date=run_date,
            source="coros",
            coros_activity_id=assignment.coros_activity_id,
            avg_pace=assignment.avg_pace,
            avg_hr=assignment.avg_hr,
            notes=assignment.notes,
        )
        db.add(db_run)
        shoe.current_mileage += assignment.distance_km
        updated_shoe_ids.add(assignment.owned_shoe_id)
        logged += 1

    db.commit()
    _set_setting(db, "last_coros_sync_at", datetime.now(timezone.utc).isoformat())

    updated_shoes: List[OwnedShoeResponse] = []
    for shoe_id in updated_shoe_ids:
        shoe = db.query(OwnedShoe).filter(OwnedShoe.id == shoe_id).first()
        if shoe:
            db.refresh(shoe)
            updated_shoes.append(_attach_computed_fields(db, shoe))

    return CorosConfirmResponse(logged=logged, updated_shoes=updated_shoes)
