from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List
from fastapi import Depends, Request
from datetime import datetime

from auth.dependencies import get_current_user_id
from models.admin_audit import AdminAudit


DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class AdminAuditService:
    """Persistent audit log service backed by SQLite."""

    def __init__(self, db_path: str | None = None):
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS admin_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor INTEGER,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """,
            )
            conn.commit()

    def log_action(self, actor: int | None, action: str, resource: str) -> AdminAudit:
        ts = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO admin_audit(actor, action, resource, timestamp) VALUES (?, ?, ?, ?)",
                (actor, action, resource, ts),
            )
            conn.commit()
        return AdminAudit(actor=actor, action=action, resource=resource, timestamp=ts)

    def query(self, skip: int = 0, limit: int = 100) -> List[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT actor, action, resource, timestamp FROM admin_audit ORDER BY id LIMIT ? OFFSET ?",
                (limit, skip),
            )
            rows = cur.fetchall()
            return [
                {"actor": r[0], "action": r[1], "resource": r[2], "timestamp": r[3]}
                for r in rows
            ]

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM admin_audit")
            conn.commit()


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
