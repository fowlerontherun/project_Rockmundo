from __future__ import annotations

import json
from typing import Dict, Optional, Tuple


def _load_events(conn) -> Dict[str, Dict]:
    """Load seasonal event configuration from app_config."""
    row = conn.execute(
        "SELECT value FROM app_config WHERE key='seasonal_events'"
    ).fetchone()
    if not row:
        return {}
    try:
        return json.loads(row["value"])
    except Exception:
        return {}


def _save_events(conn, events: Dict[str, Dict]) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO app_config(key, value) VALUES('seasonal_events', ?)",
        (json.dumps(events, ensure_ascii=False),),
    )


class SeasonScheduler:
    """Simple loader to compute active seasonal score multipliers."""

    def __init__(self, conn) -> None:
        self.conn = conn
        self.events = _load_events(conn)

    def active_season(self, day: str) -> Tuple[Optional[str], float]:
        """Return the active season and multiplier for ``day``."""
        for name, cfg in self.events.items():
            start = cfg.get("start")
            end = cfg.get("end")
            if not (start and end):
                continue
            if not cfg.get("active", False):
                continue
            if start <= day <= end:
                return name, float(cfg.get("multiplier", 1.0))
        return None, 1.0


def activate_season(conn, season: str) -> bool:
    events = _load_events(conn)
    if season not in events:
        return False
    events[season]["active"] = True
    _save_events(conn, events)
    return True


def deactivate_season(conn, season: str) -> bool:
    events = _load_events(conn)
    if season not in events:
        return False
    events[season]["active"] = False
    _save_events(conn, events)
    return True
