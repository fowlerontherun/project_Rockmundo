"""Service for handling item shipments between city shops."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class ShippingService:
    """Manage inter-city transfers of shop items with fees and transit times."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        """Ensure the shipments table exists."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS shipments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_shop_id INTEGER NOT NULL,
                    dest_shop_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    fee_cents INTEGER NOT NULL,
                    transit_hours INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'in_transit',
                    created_at TEXT DEFAULT (datetime('now')),
                    arrival_time TEXT NOT NULL,
                    FOREIGN KEY(source_shop_id) REFERENCES city_shops(id),
                    FOREIGN KEY(dest_shop_id) REFERENCES city_shops(id)
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _shop_city(self, shop_id: int) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT city FROM city_shops WHERE id = ?", (shop_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def _calculate_transit(self, src_city: str, dest_city: str) -> int:
        return 24 if src_city == dest_city else 72

    def _calculate_fee(self, quantity: int, src_city: str, dest_city: str) -> int:
        fee = quantity * 100
        if src_city != dest_city:
            fee += 500
        return fee

    def _refresh_status(self, conn: sqlite3.Connection) -> None:
        cur = conn.cursor()
        cur.execute(
            "UPDATE shipments SET status='delivered' WHERE status='in_transit' AND arrival_time <= datetime('now')"
        )
        conn.commit()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def create_shipment(
        self, source_shop_id: int, dest_shop_id: int, item_id: int, quantity: int
    ) -> Dict[str, Any]:
        src_city = self._shop_city(source_shop_id)
        dest_city = self._shop_city(dest_shop_id)
        if not src_city or not dest_city:
            raise ValueError("Invalid shop id")
        transit_hours = self._calculate_transit(src_city, dest_city)
        fee = self._calculate_fee(quantity, src_city, dest_city)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO shipments (
                    source_shop_id, dest_shop_id, item_id, quantity,
                    fee_cents, transit_hours, arrival_time
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now', ?))
                """,
                (
                    source_shop_id,
                    dest_shop_id,
                    item_id,
                    quantity,
                    fee,
                    transit_hours,
                    f"+{transit_hours} hours",
                ),
            )
            sid = int(cur.lastrowid or 0)
            conn.commit()
        return self.get_shipment(sid) or {}

    def get_shipment(self, shipment_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            self._refresh_status(conn)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_shipments(self, shop_id: int | None = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            self._refresh_status(conn)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            query = "SELECT * FROM shipments"
            params: List[Any] = []
            if shop_id is not None:
                query += " WHERE source_shop_id = ? OR dest_shop_id = ?"
                params = [shop_id, shop_id]
            query += " ORDER BY created_at DESC"
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
