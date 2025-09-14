from __future__ import annotations

import sqlite3
from typing import List, Optional

from database import DB_PATH
from backend.models.workshop import Workshop


class WorkshopAdminService:
    """CRUD helpers for workshop events stored in SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    # ------------------------------------------------------------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS workshops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_target TEXT NOT NULL,
                    xp_reward INTEGER NOT NULL,
                    ticket_price INTEGER NOT NULL,
                    schedule TEXT NOT NULL
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    def list_workshops(self) -> List[Workshop]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, skill_target, xp_reward, ticket_price, schedule FROM workshops ORDER BY id"
            )
            rows = cur.fetchall()
            return [Workshop(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    def create_workshop(self, ws: Workshop) -> Workshop:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO workshops (skill_target, xp_reward, ticket_price, schedule) VALUES (?, ?, ?, ?)",
                (ws.skill_target, ws.xp_reward, ws.ticket_price, ws.schedule),
            )
            ws.id = cur.lastrowid
            conn.commit()
            return ws

    # ------------------------------------------------------------------
    def update_workshop(self, workshop_id: int, **changes) -> Workshop:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, skill_target, xp_reward, ticket_price, schedule FROM workshops WHERE id = ?",
                (workshop_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("workshop_not_found")
            data = dict(row)
            for k, v in changes.items():
                if k in data and v is not None:
                    data[k] = v
            cur.execute(
                "UPDATE workshops SET skill_target=?, xp_reward=?, ticket_price=?, schedule=? WHERE id=?",
                (
                    data["skill_target"],
                    data["xp_reward"],
                    data["ticket_price"],
                    data["schedule"],
                    workshop_id,
                ),
            )
            conn.commit()
            return Workshop(**data)

    # ------------------------------------------------------------------
    def delete_workshop(self, workshop_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM workshops WHERE id=?", (workshop_id,))
            conn.commit()

    # ------------------------------------------------------------------
    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM workshops")
            conn.commit()


workshop_admin_service = WorkshopAdminService()


def get_workshop_admin_service() -> WorkshopAdminService:
    return workshop_admin_service


__all__ = ["WorkshopAdminService", "workshop_admin_service", "get_workshop_admin_service"]
