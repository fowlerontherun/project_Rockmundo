"""Admin system monitoring routes."""
from __future__ import annotations

from fastapi import APIRouter, Request

from auth.dependencies import get_current_user_id, require_permission
from models.admin import admin_sessions

try:  # optional psutil, fall back to zeros if unavailable
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore

router = APIRouter(prefix="/monitoring", tags=["AdminMonitoring"])


@router.get("/metrics")
async def metrics(req: Request) -> dict[str, float | int]:
    """Return basic CPU, memory, and active admin session counts."""
    admin_id = await get_current_user_id(req)
    await require_permission(["admin", "moderator"], admin_id)

    cpu = psutil.cpu_percent(interval=0.1) if psutil else 0.0
    mem = psutil.virtual_memory().percent if psutil else 0.0
    active = sum(1 for s in admin_sessions.values() if not s.is_expired())
    return {"cpu": cpu, "memory": mem, "active_sessions": active}
