# File: backend/services/sales_service.py
"""
SalesService (Digital & Vinyl)
------------------------------
Sync sqlite3 service providing:
- Digital purchases for songs/albums
- Vinyl SKU inventory, orders, refunds

Tables created (if missing):
- digital_sales
- vinyl_skus
- vinyl_orders
- vinyl_order_items
- vinyl_refunds
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

@dataclass
class VinylItem:
    sku_id: int
    qty: int

class SalesError(Exception):
    pass

class SalesService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # ------------- Schema -------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            # Digital sales (song/album)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS digital_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_user_id INTEGER NOT NULL,
                work_type TEXT NOT NULL,           -- 'song' | 'album'
                work_id INTEGER NOT NULL,
                price_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                source TEXT,                       -- 'store','promo','bundle', etc.
                created_at TEXT DEFAULT (datetime('now'))
            )
            """)

            # Vinyl SKUs (inventory per variant)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS vinyl_skus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                album_id INTEGER NOT NULL,
                variant TEXT NOT NULL,             -- e.g., 'Black 180g', 'Marbled Blue'
                price_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                stock_qty INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
            """)

            # Vinyl Orders header
            cur.execute("""
            CREATE TABLE IF NOT EXISTS vinyl_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_user_id INTEGER NOT NULL,
                total_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT NOT NULL DEFAULT 'confirmed',  -- pending|confirmed|refunded|cancelled
                shipping_address TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
            """)

            # Vinyl Order items
            cur.execute("""
            CREATE TABLE IF NOT EXISTS vinyl_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                sku_id INTEGER NOT NULL,
                unit_price_cents INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                refunded_qty INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(order_id) REFERENCES vinyl_orders(id),
                FOREIGN KEY(sku_id) REFERENCES vinyl_skus(id)
            )
            """)

            # Vinyl refunds
            cur.execute("""
            CREATE TABLE IF NOT EXISTS vinyl_refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount_cents INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(order_id) REFERENCES vinyl_orders(id)
            )
            """)

            # Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS ix_digital_sales_work ON digital_sales(work_type, work_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_vinyl_skus_album ON vinyl_skus(album_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_vinyl_items_order ON vinyl_order_items(order_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_vinyl_items_sku ON vinyl_order_items(sku_id)")

            conn.commit()

    # ------------- Helpers -------------
    def _now(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # ------------- Digital -------------
    def record_digital_sale(
        self,
        buyer_user_id: int,
        work_type: str,     # 'song' | 'album'
        work_id: int,
        price_cents: int,
        currency: str = "USD",
        source: Optional[str] = "store",
    ) -> int:
        work_type = work_type.lower()
        if work_type not in ("song", "album"):
            raise SalesError("work_type must be 'song' or 'album'")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO digital_sales (buyer_user_id, work_type, work_id, price_cents, currency, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (buyer_user_id, work_type, work_id, price_cents, currency, source))
            conn.commit()
            return cur.lastrowid

    def list_digital_sales_for_work(self, work_type: str, work_id: int) -> List[Dict[str, Any]]:
        work_type = work_type.lower()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM digital_sales
                WHERE work_type = ? AND work_id = ?
                ORDER BY created_at DESC
            """, (work_type, work_id))
            return [dict(r) for r in cur.fetchall()]

    # ------------- Vinyl SKUs -------------
    def create_vinyl_sku(self, album_id: int, variant: str, price_cents: int, stock_qty: int, currency: str = "USD") -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO vinyl_skus (album_id, variant, price_cents, currency, stock_qty)
                VALUES (?, ?, ?, ?, ?)
            """, (album_id, variant, price_cents, currency, stock_qty))
            conn.commit()
            return cur.lastrowid

    def list_vinyl_skus(self, album_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM vinyl_skus WHERE album_id = ? ORDER BY price_cents ASC", (album_id,))
            return [dict(r) for r in cur.fetchall()]

    def update_vinyl_sku(self, sku_id: int, **fields) -> None:
        if not fields:
            return
        cols, vals = [], []
        for k in ("variant","price_cents","currency","stock_qty"):
            if k in fields:
                cols.append(f"{k} = ?")
                vals.append(fields[k])
        if not cols:
            return
        vals.append(sku_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE vinyl_skus SET {', '.join(cols)}, updated_at = datetime('now') WHERE id = ?", vals)
            conn.commit()

    def _sku_remaining(self, cur, sku_id: int) -> int:
        cur.execute("""
            SELECT
              s.stock_qty
              - IFNULL((
                SELECT SUM(oi.qty - oi.refunded_qty)
                FROM vinyl_order_items oi
                JOIN vinyl_orders o ON o.id = oi.order_id
                WHERE oi.sku_id = s.id AND o.status IN ('confirmed','pending')
              ), 0) AS remaining
            FROM vinyl_skus s
            WHERE s.id = ?
        """, (sku_id,))
        row = cur.fetchone()
        return int(row[0] if row and row[0] is not None else 0)

    # ------------- Vinyl Purchases -------------
    def purchase_vinyl(self, buyer_user_id: int, items: List[Dict[str, int]], shipping_address: Optional[str] = None) -> int:
        norm_items = [VinylItem(int(x["sku_id"]), int(x["qty"])) for x in items if int(x.get("qty", 0)) > 0]
        if not norm_items:
            raise SalesError("No vinyl items specified")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")

                # Validate & price
                total_cents = 0
                currency = "USD"
                for it in norm_items:
                    cur.execute("SELECT * FROM vinyl_skus WHERE id = ?", (it.sku_id,))
                    sku = cur.fetchone()
                    if not sku:
                        raise SalesError("SKU not found")
                    remaining = self._sku_remaining(cur, it.sku_id)
                    if remaining < it.qty:
                        raise SalesError(f"Not enough stock for variant '{sku['variant']}'")
                    total_cents += int(sku["price_cents"]) * it.qty
                    currency = sku["currency"] or currency

                # Create order
                cur.execute("""
                    INSERT INTO vinyl_orders (buyer_user_id, total_cents, currency, status, shipping_address)
                    VALUES (?, ?, ?, 'confirmed', ?)
                """, (buyer_user_id, total_cents, currency, shipping_address))
                order_id = cur.lastrowid

                # Items
                for it in norm_items:
                    cur.execute("SELECT price_cents FROM vinyl_skus WHERE id = ?", (it.sku_id,))
                    price = int(cur.fetchone()[0])
                    cur.execute("""
                        INSERT INTO vinyl_order_items (order_id, sku_id, unit_price_cents, qty)
                        VALUES (?, ?, ?, ?)
                    """, (order_id, it.sku_id, price, it.qty))

                conn.commit()
                return order_id
            except Exception:
                conn.rollback()
                raise

    def refund_vinyl_order(self, order_id: int, reason: str = "") -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM vinyl_orders WHERE id = ?", (order_id,))
            order = cur.fetchone()
            if not order:
                raise SalesError("Order not found")
            if order["status"] == "refunded":
                raise SalesError("Order already refunded")

            cur.execute("""
                SELECT SUM(unit_price_cents * (qty - refunded_qty)) AS refundable
                FROM vinyl_order_items
                WHERE order_id = ?
            """, (order_id,))
            row = cur.fetchone()
            refundable = int(row["refundable"] or 0)
            if refundable <= 0:
                raise SalesError("Nothing to refund")

            try:
                cur.execute("BEGIN IMMEDIATE")
                cur.execute("UPDATE vinyl_orders SET status = 'refunded', updated_at = datetime('now') WHERE id = ?", (order_id,))
                cur.execute("UPDATE vinyl_order_items SET refunded_qty = qty WHERE order_id = ?", (order_id,))
                cur.execute("""
                    INSERT INTO vinyl_refunds (order_id, amount_cents, reason)
                    VALUES (?, ?, ?)
                """, (order_id, refundable, reason))
                conn.commit()
                return {"order_id": order_id, "refunded_cents": refundable}
            except Exception:
                conn.rollback()
                raise

    # ------------- Queries -------------
    def get_vinyl_order(self, order_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM vinyl_orders WHERE id = ?", (order_id,))
            o = cur.fetchone()
            if not o:
                raise SalesError("Order not found")
            cur.execute("""
                SELECT oi.*, s.variant
                FROM vinyl_order_items oi
                JOIN vinyl_skus s ON s.id = oi.sku_id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = [dict(r) for r in cur.fetchall()]
            d = dict(o)
            d["items"] = items
            return d

    def list_vinyl_orders_for_user(self, buyer_user_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM vinyl_orders WHERE buyer_user_id = ? ORDER BY created_at DESC", (buyer_user_id,))
            return [dict(r) for r in cur.fetchall()]
