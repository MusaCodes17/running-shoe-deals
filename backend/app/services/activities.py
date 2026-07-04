"""
Unified activity feed (§3 Phase-3a).

Two run stores exist: `strava_activities` (frozen at the Jul 2026 bulk
export) and `shoe_runs` (live — COROS / manual / Strava-backfill). New runs
land only in `shoe_runs`, so any Training view reading `strava_activities`
alone goes stale immediately. This service unions them into one date-sorted
feed the whole app (web + MCP + future mobile) reads through.

Union semantics:
- Start from `strava_activities` (runs only), LEFT-joined to `shoe_runs` via
  `shoe_runs.strava_activity_id` — a linked run gives shoe attribution and is
  NOT double-counted (it appears once, on the Strava side).
- Add `shoe_runs` rows with `strava_activity_id IS NULL` — post-export COROS/
  manual runs and any unlinked history.

The canonical `activities` table (§3 Phase-5) can replace the internals here
without the UI ever noticing — that's the whole point of this seam.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import OwnedShoe, ShoeRun, StravaActivity
from app.services import rotation


@dataclass
class UnifiedShoe:
    id: int
    brand: str
    model: str
    nickname: Optional[str] = None


@dataclass
class UnifiedActivity:
    date: date
    distance_km: float
    source: str                         # "strava" | "coros" | "manual"
    moving_time_s: Optional[int] = None
    avg_pace: Optional[str] = None      # "M:SS/km"
    avg_pace_s_per_km: Optional[int] = None
    avg_hr: Optional[int] = None
    elevation_m: Optional[float] = None
    name: Optional[str] = None
    shoe: Optional[UnifiedShoe] = None
    strava_activity_id: Optional[int] = None
    shoe_run_id: Optional[int] = None

    @property
    def _sort_key(self):
        # Deterministic tiebreak so pagination is stable when two runs share a
        # date (which is common — Strava stores date only, no time here).
        return (self.date, self.strava_activity_id or 0, self.shoe_run_id or 0)


def _effective_moving_s(a: UnifiedActivity) -> Optional[float]:
    """Seconds used for distance-weighted pace: real moving time when we have
    it (Strava), else reconstructed from the run's average pace."""
    if a.moving_time_s and a.distance_km:
        return float(a.moving_time_s)
    if a.avg_pace_s_per_km and a.distance_km:
        return a.avg_pace_s_per_km * a.distance_km
    return None


def _build(db: Session) -> list[UnifiedActivity]:
    """The raw union, unsorted/unfiltered. Split out so stats helpers can reuse
    it without re-implementing the join."""
    shoes = {s.id: s for s in db.query(OwnedShoe).all()}

    def _shoe_of(run: ShoeRun) -> Optional[UnifiedShoe]:
        s = shoes.get(run.owned_shoe_id)
        if s is None:
            return None
        return UnifiedShoe(id=s.id, brand=s.brand, model=s.model, nickname=s.nickname)

    runs = db.query(ShoeRun).all()
    linked_by_said: dict[int, ShoeRun] = {}
    unlinked: list[ShoeRun] = []
    for run in runs:
        if run.strava_activity_id is not None:
            linked_by_said[run.strava_activity_id] = run
        else:
            unlinked.append(run)

    out: list[UnifiedActivity] = []

    # Strava side (runs only). A linked shoe_run only supplies attribution.
    for sa in (
        db.query(StravaActivity)
        .filter(StravaActivity.activity_type == "Run")
        .all()
    ):
        if sa.run_date is None:
            continue
        linked = linked_by_said.get(sa.strava_activity_id)
        pace_s = sa.avg_pace_s_per_km
        out.append(UnifiedActivity(
            date=sa.run_date,
            distance_km=sa.distance_km or 0.0,
            source="strava",
            moving_time_s=sa.moving_time_s,
            avg_pace=rotation.seconds_to_pace(pace_s) if pace_s else None,
            avg_pace_s_per_km=pace_s,
            avg_hr=sa.avg_hr,
            elevation_m=sa.elevation_gain_m,
            name=sa.name,
            shoe=_shoe_of(linked) if linked else None,
            strava_activity_id=sa.strava_activity_id,
            shoe_run_id=linked.id if linked else None,
        ))

    # shoe_runs side: only the unlinked ones (post-export COROS/manual/etc.).
    for run in unlinked:
        if run.run_date is None:
            continue
        pace_s = rotation.pace_to_seconds(run.avg_pace) if run.avg_pace else None
        out.append(UnifiedActivity(
            date=run.run_date,
            distance_km=run.distance_km or 0.0,
            source=run.source or "manual",
            avg_pace=run.avg_pace,
            avg_pace_s_per_km=int(pace_s) if pace_s else None,
            avg_hr=run.avg_hr,
            shoe=_shoe_of(run),
            shoe_run_id=run.id,
        ))

    return out


def unified_activities(
    db: Session,
    *,
    year: Optional[int] = None,
    month: Optional[int] = None,
    shoe_id: Optional[int] = None,
    min_distance_km: Optional[float] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> list[UnifiedActivity]:
    """
    The unioned run feed, newest first, with optional filters and stable
    limit/offset pagination.

    `min_distance_km` is an extension over the §3 signature so the Training
    activities list can filter short runs server-side (keeping it consistent
    with server-side pagination rather than filtering a single page in React).
    """
    items = _build(db)

    if year is not None:
        items = [a for a in items if a.date.year == year]
    if month is not None:
        items = [a for a in items if a.date.month == month]
    if shoe_id is not None:
        items = [a for a in items if a.shoe is not None and a.shoe.id == shoe_id]
    if min_distance_km is not None:
        items = [a for a in items if a.distance_km >= min_distance_km]

    items.sort(key=lambda a: a._sort_key, reverse=True)

    if offset:
        items = items[offset:]
    if limit is not None:
        items = items[:limit]
    return items
