"""
COROS API client utilities shared between the REST router and MCP tools.

Only handles HTTP communication and unit conversion — no DB access here.
"""
import os
import time
from datetime import datetime, timezone
from typing import Optional

import requests

COROS_BASE_URL = "https://open.coros.com"
RUNNING_SPORT_TYPES = {100, 101, 102, 103}


def get_coros_config() -> Optional[dict]:
    """
    Read COROS credentials from env vars. Returns None if the minimum
    required vars (COROS_ACCESS_TOKEN, COROS_OPEN_ID) are absent, which
    means the sync feature is disabled.
    """
    access_token = os.getenv("COROS_ACCESS_TOKEN", "").strip()
    open_id = os.getenv("COROS_OPEN_ID", "").strip()
    if not access_token or not open_id:
        return None
    return {
        "client_id": os.getenv("COROS_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("COROS_CLIENT_SECRET", "").strip(),
        "access_token": access_token,
        "open_id": open_id,
    }


def seconds_to_pace(seconds_per_km: int) -> str:
    """Convert a raw COROS avgPace value (seconds/km) to 'M:SS/km'."""
    mins, secs = divmod(int(seconds_per_km), 60)
    return f"{mins}:{secs:02d}/km"


def fetch_running_activities(config: dict, days_back: int) -> list:
    """
    Call the COROS sport list endpoint and return raw activity dicts
    filtered to running sport types within the requested date window.

    Raises requests.HTTPError on network/API errors, ValueError on
    COROS-level errors (non-zero result code).
    """
    cutoff = int(time.time()) - days_back * 86400

    headers = {
        "Authorization": f"Bearer {config['access_token']}",
        "Content-Type": "application/json",
    }
    body = {
        "size": 100,
        "pageIndex": 1,
        "openId": config["open_id"],
    }

    resp = requests.post(
        f"{COROS_BASE_URL}/v2/coros/sport/list",
        headers=headers,
        json=body,
        timeout=15,
    )

    if resp.status_code == 401:
        raise ValueError("COROS credentials invalid. Check COROS_ACCESS_TOKEN and COROS_OPEN_ID in your .env.")
    resp.raise_for_status()

    data = resp.json()
    result_code = str(data.get("result", ""))
    if result_code not in ("0000", "0"):
        raise ValueError(f"COROS API error ({result_code}): {data.get('message', 'Unknown error')}")

    activities = data.get("data", {}).get("list", [])
    return [
        a for a in activities
        if a.get("sportType") in RUNNING_SPORT_TYPES
        and a.get("startTime", 0) >= cutoff
    ]


def activity_to_run_dict(activity: dict) -> dict:
    """Normalize a raw COROS activity dict into a clean run representation."""
    raw_pace = activity.get("avgPace")
    avg_hr_raw = activity.get("avgHr")
    start_ts = activity.get("startTime", 0)
    return {
        "coros_activity_id": str(activity.get("labelId", "")),
        "date": datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime("%Y-%m-%d"),
        "distance_km": round(activity.get("totalDistance", 0) / 1000, 2),
        "avg_pace": seconds_to_pace(raw_pace) if raw_pace else None,
        "avg_hr": int(avg_hr_raw) if avg_hr_raw else None,
        "sport_type": activity.get("sportType", 100),
        "name": activity.get("name") or "Run",
    }
