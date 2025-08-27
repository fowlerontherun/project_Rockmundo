from __future__ import annotations

from dataclasses import asdict
from typing import List
from fastapi import Depends, Request
from datetime import datetime

from backend.auth.dependencies import get_current_user_id
from backend.models.admin_audit import AdminAudit


class AdminAuditService:
    """Simple in-memory audit log service."""

    def __init__(self):
        self._logs: List[AdminAudit] = []

    def log_action(self, actor: int | None, action: str, resource: str) -> AdminAudit:
        entry = AdminAudit(actor=actor, action=action, resource=resource, timestamp=datetime.utcnow().isoformat())
        self._logs.append(entry)
        return entry

    def query(self, skip: int = 0, limit: int = 100) -> List[dict]:
        return [log.to_dict() for log in self._logs[skip : skip + limit]]

    def clear(self) -> None:
        self._logs.clear()


audit_service = AdminAuditService()


def get_admin_audit_service() -> AdminAuditService:
    return audit_service


async def audit_dependency(
    req: Request, svc: AdminAuditService = Depends(get_admin_audit_service)
) -> None:
    """FastAPI dependency to automatically log admin actions."""
    try:
        actor = await get_current_user_id(req)
    except Exception:
        actor = None
    svc.log_action(actor, req.method, req.url.path)
