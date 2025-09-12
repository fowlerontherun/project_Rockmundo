"""Admin system monitoring routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

try:  # pragma: no cover - optional auth dependency
    from backend.auth.dependencies import get_current_user_id, require_permission
except Exception:  # pragma: no cover
    async def get_current_user_id(req: Request) -> int:  # type: ignore
        header = req.headers.get("X-User-Id")
        if header and header.isdigit():
            return int(header)
        raise HTTPException(status_code=401, detail="Missing auth")

    async def require_permission(roles, user_id):  # type: ignore
        if user_id != 1:
            raise HTTPException(status_code=403, detail="Forbidden")
        return True
from models.admin import admin_sessions
from services.session_service import SessionService, get_session_service

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


@router.get("/permissions")
async def permissions(req: Request) -> dict[str, bool]:
    """Return whether the current user may access admin dashboards."""
    admin_id = await get_current_user_id(req)
    await require_permission(["admin", "moderator"], admin_id)
    return {"allowed": True}


@router.get("/sessions")
async def list_sessions(
    req: Request,
    svc: SessionService = Depends(get_session_service),
) -> list[dict]:
    """Return all active sessions."""
    admin_id = await get_current_user_id(req)
    await require_permission(["admin", "moderator"], admin_id)
    return svc.list_sessions()


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    req: Request,
    svc: SessionService = Depends(get_session_service),
) -> dict[str, str]:
    """Terminate a session by ID."""
    admin_id = await get_current_user_id(req)
    await require_permission(["admin", "moderator"], admin_id)
    if not svc.terminate_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "terminated"}
