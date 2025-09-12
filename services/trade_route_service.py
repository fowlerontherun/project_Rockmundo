"""Service to schedule trade shipments applying taxes or tariffs."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class TradeRouteService:
    """Manage city-to-city trade routes with fees and transit times."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        """Ensure the trade routes table exists."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_city TEXT NOT NULL,
                    dest_city TEXT NOT NULL,
                    goods TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    value_cents INTEGER NOT NULL,
                    tax_cents INTEGER NOT NULL,
                    total_cents INTEGER NOT NULL,
                    transit_hours INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'in_transit',
                    created_at TEXT DEFAULT (datetime('now')),
                    arrival_time TEXT NOT NULL
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _calculate_transit(self, src: str, dest: str) -> int:
        return 24 if src == dest else 72

    def _calculate_tax(self, value: int, src: str, dest: str) -> int:
        rate = 0.0 if src == dest else 0.1
        return int(value * rate)

    def _refresh_status(self, conn: sqlite3.Connection) -> None:
        cur = conn.cursor()
        cur.execute(
            "UPDATE trade_routes SET status='delivered' WHERE status='in_transit' AND arrival_time <= datetime('now')"
        )
        conn.commit()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def schedule_trade(
        self, source_city: str, dest_city: str, goods: str, quantity: int, value_cents: int
    ) -> Dict[str, Any]:
        transit_hours = self._calculate_transit(source_city, dest_city)
        tax = self._calculate_tax(value_cents, source_city, dest_city)
        total = value_cents + tax
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO trade_routes (
                    source_city, dest_city, goods, quantity,
                    value_cents, tax_cents, total_cents,
                    transit_hours, arrival_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', ?))
                """,
                (
                    source_city,
                    dest_city,
                    goods,
                    quantity,
                    value_cents,
                    tax,
                    total,
                    transit_hours,
                    f"+{transit_hours} hours",
                ),
            )
            rid = int(cur.lastrowid or 0)
            conn.commit()
        return self.get_route(rid) or {}

    def get_route(self, route_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            self._refresh_status(conn)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM trade_routes WHERE id = ?", (route_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_routes(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            self._refresh_status(conn)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM trade_routes ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]
