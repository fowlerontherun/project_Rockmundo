"""API endpoints exposing basic service metrics."""

from __future__ import annotations

import os
import resource
from typing import Any, Dict

from fastapi import APIRouter

try:  # FastAPI stub in tests may not expose Depends
    from fastapi import Depends
except Exception:  # pragma: no cover - fallback for stubs
    def Depends(dependency: Any) -> Any:  # type: ignore[misc]
        return dependency

from auth.dependencies import require_permission
from utils.db import get_conn

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/health")
def health(
    _: bool = Depends(require_permission(["admin"])),
    conn: Any = Depends(get_conn),
) -> Dict[str, Any]:
    """Return basic application health information.

    A simple query is executed to confirm database connectivity. The database
    connection is closed after use.
    """
    row = conn.execute("SELECT datetime('now') AS now").fetchone()
    conn.close()
    return {"status": "ok", "db_time": row["now"]}


@router.get("/performance")
def performance(_: bool = Depends(require_permission(["admin"]))) -> Dict[str, Any]:
    """Return lightweight process performance metrics."""
    load1, load5, load15 = os.getloadavg()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "load_average": {"1m": load1, "5m": load5, "15m": load15},
        "memory": {"rss_kb": usage.ru_maxrss},
    }

