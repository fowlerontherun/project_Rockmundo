# File: backend/services/sales_service.py
import sqlite3
from dataclasses import dataclass

try:  # pragma: no cover - prefer local stub if available
    import utils.aiosqlite_local as aiosqlite
except ModuleNotFoundError:  # pragma: no cover - fallback to package
    import aiosqlite  # type: ignore
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from services.song_popularity_service import add_event
from services.economy_service import EconomyService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

@dataclass
class VinylItem:
    sku_id: int
    qty: int

class SalesError(Exception):
    pass

class SalesService:
    def __init__(self, db_path: Optional[str] = None, economy: Optional[EconomyService] = None):
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(self.db_path)

    async def ensure_schema(self) -> None:
        conn = await aiosqlite.connect(self.db_path)
        try:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS digital_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_user_id INTEGER NOT NULL,
                work_type TEXT NOT NULL,
                work_id INTEGER NOT NULL,
                price_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                source TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """)
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS vinyl_skus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                album_id INTEGER NOT NULL,
                variant TEXT NOT NULL,
                price_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                stock_qty INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
            """)
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS vinyl_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_user_id INTEGER NOT NULL,
                total_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT NOT NULL DEFAULT 'confirmed',
                shipping_address TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
            """)
            await conn.execute("""
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
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS vinyl_refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount_cents INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(order_id) REFERENCES vinyl_orders(id)
            )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS ix_digital_sales_work ON digital_sales(work_type, work_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS ix_vinyl_skus_album ON vinyl_skus(album_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS ix_vinyl_items_order ON vinyl_order_items(order_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS ix_vinyl_items_sku ON vinyl_order_items(sku_id)")
            await conn.commit()
        finally:
            await conn.close()

    def _now(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    async def record_digital_sale(
        self,
        buyer_user_id: int,
        work_type: str,
        work_id: int,
        price_cents: int,
        currency: str = "USD",
        source: Optional[str] = "store",
        album_type: Optional[str] = None,
    ) -> int:
        work_type = work_type.lower()
        if work_type not in ("song", "album"):
            raise SalesError("work_type must be 'song' or 'album'")

        band_id: Optional[int] = None
        if work_type == "album":
            album_type = (album_type or "studio").lower()
            if album_type not in ("studio", "live"):
                raise SalesError("album_type must be 'studio' or 'live'")

        conn = await aiosqlite.connect(self.db_path)
        try:
            cur = await conn.execute(
                """
                INSERT INTO digital_sales (buyer_user_id, work_type, work_id, price_cents, currency, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (buyer_user_id, work_type, work_id, price_cents, currency, source),
            )

            if work_type == "album":
                try:
                    band_cur = await conn.execute("SELECT band_id FROM releases WHERE id = ?", (work_id,))
                    row = await band_cur.fetchone()
                    if row and row[0] is not None:
                        band_id = int(row[0])
                except sqlite3.OperationalError:
                    band_id = None

            await conn.commit()
            sale_id = cur.lastrowid
        finally:
            await conn.close()

        if work_type == "song":
            add_event(work_id, price_cents / 100.0, "sale")

        if work_type == "album" and band_id is not None:
            try:
                self.economy.deposit(band_id, price_cents, currency)
            except Exception:
                pass

        return sale_id

    async def list_digital_sales_for_work(self, work_type: str, work_id: int) -> List[Dict[str, Any]]:
        work_type = work_type.lower()
        conn = await aiosqlite.connect(self.db_path)
        try:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                """
                SELECT * FROM digital_sales
                WHERE work_type = ? AND work_id = ?
                ORDER BY created_at DESC
                """,
                (work_type, work_id),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await conn.close()

    async def create_vinyl_sku(self, album_id: int, variant: str, price_cents: int, stock_qty: int, currency: str = "USD") -> int:
        conn = await aiosqlite.connect(self.db_path)
        try:
            cur = await conn.execute(
                """
                INSERT INTO vinyl_skus (album_id, variant, price_cents, currency, stock_qty)
                VALUES (?, ?, ?, ?, ?)
                """,
                (album_id, variant, price_cents, currency, stock_qty),
            )
            await conn.commit()
            return cur.lastrowid
        finally:
            await conn.close()

    async def list_vinyl_skus(self, album_id: int) -> List[Dict[str, Any]]:
        conn = await aiosqlite.connect(self.db_path)
        try:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM vinyl_skus WHERE album_id = ? ORDER BY price_cents ASC",
                (album_id,),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await conn.close()

    async def update_vinyl_sku(self, sku_id: int, **fields) -> None:
        if not fields:
            return
        cols, vals = [], []
        for k in ("variant", "price_cents", "currency", "stock_qty"):
            if k in fields:
                cols.append(f"{k} = ?")
                vals.append(fields[k])
        if not cols:
            return
        vals.append(sku_id)
        conn = await aiosqlite.connect(self.db_path)
        try:
            await conn.execute(
                f"UPDATE vinyl_skus SET {', '.join(cols)}, updated_at = datetime('now') WHERE id = ?",
                vals,
            )
            await conn.commit()
        finally:
            await conn.close()

    async def _sku_remaining(self, conn: aiosqlite.Connection, sku_id: int) -> int:
        cur = await conn.execute(
            """
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
            """,
            (sku_id,),
        )
        row = await cur.fetchone()
        return int(row[0] if row and row[0] is not None else 0)

    async def purchase_vinyl(self, buyer_user_id: int, items: List[Dict[str, int]], shipping_address: Optional[str] = None) -> int:
        norm_items = [VinylItem(int(x["sku_id"]), int(x["qty"])) for x in items if int(x.get("qty", 0)) > 0]
        if not norm_items:
            raise SalesError("No vinyl items specified")

        conn = await aiosqlite.connect(self.db_path)
        try:
            conn.row_factory = aiosqlite.Row
            await conn.execute("BEGIN IMMEDIATE")
            total_cents = 0
            currency = "USD"
            for it in norm_items:
                cur = await conn.execute("SELECT * FROM vinyl_skus WHERE id = ?", (it.sku_id,))
                sku = await cur.fetchone()
                if not sku:
                    raise SalesError("SKU not found")
                remaining = await self._sku_remaining(conn, it.sku_id)
                if remaining < it.qty:
                    raise SalesError(f"Not enough stock for variant '{sku['variant']}'")
                total_cents += int(sku["price_cents"]) * it.qty
                currency = sku["currency"] or currency

            cur = await conn.execute(
                """
                INSERT INTO vinyl_orders (buyer_user_id, total_cents, currency, status, shipping_address)
                VALUES (?, ?, ?, 'confirmed', ?)
                """,
                (buyer_user_id, total_cents, currency, shipping_address),
            )
            order_id = cur.lastrowid

            for it in norm_items:
                price_cur = await conn.execute("SELECT price_cents FROM vinyl_skus WHERE id = ?", (it.sku_id,))
                price = int((await price_cur.fetchone())[0])
                await conn.execute(
                    """
                    INSERT INTO vinyl_order_items (order_id, sku_id, unit_price_cents, qty)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, it.sku_id, price, it.qty),
                )

            await conn.commit()
            return order_id
        except Exception:
            await conn.rollback()
            raise
        finally:
            await conn.close()

    async def refund_vinyl_order(self, order_id: int, reason: str = "") -> Dict[str, Any]:
        conn = await aiosqlite.connect(self.db_path)
        try:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM vinyl_orders WHERE id = ?", (order_id,))
            order = await cur.fetchone()
            if not order:
                raise SalesError("Order not found")
            if order["status"] == "refunded":
                raise SalesError("Order already refunded")

            cur = await conn.execute(
                """
                SELECT SUM(unit_price_cents * (qty - refunded_qty)) AS refundable
                FROM vinyl_order_items
                WHERE order_id = ?
                """,
                (order_id,),
            )
            row = await cur.fetchone()
            refundable = int(row["refundable"] or 0)
            if refundable <= 0:
                raise SalesError("Nothing to refund")

            try:
                await conn.execute("BEGIN IMMEDIATE")
                await conn.execute("UPDATE vinyl_orders SET status = 'refunded', updated_at = datetime('now') WHERE id = ?", (order_id,))
                await conn.execute("UPDATE vinyl_order_items SET refunded_qty = qty WHERE order_id = ?", (order_id,))
                await conn.execute(
                    """
                    INSERT INTO vinyl_refunds (order_id, amount_cents, reason)
                    VALUES (?, ?, ?)
                    """,
                    (order_id, refundable, reason),
                )
                await conn.commit()
                return {"order_id": order_id, "refunded_cents": refundable}
            except Exception:
                await conn.rollback()
                raise
        finally:
            await conn.close()

    async def get_vinyl_order(self, order_id: int) -> Dict[str, Any]:
        conn = await aiosqlite.connect(self.db_path)
        try:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM vinyl_orders WHERE id = ?", (order_id,))
            o = await cur.fetchone()
            if not o:
                raise SalesError("Order not found")
            cur = await conn.execute(
                """
                SELECT oi.*, s.variant
                FROM vinyl_order_items oi
                JOIN vinyl_skus s ON s.id = oi.sku_id
                WHERE oi.order_id = ?
                """,
                (order_id,),
            )
            items = [dict(r) for r in await cur.fetchall()]
            d = dict(o)
            d["items"] = items
            return d
        finally:
            await conn.close()

    async def list_vinyl_orders_for_user(self, buyer_user_id: int) -> List[Dict[str, Any]]:
        conn = await aiosqlite.connect(self.db_path)
        try:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM vinyl_orders WHERE buyer_user_id = ? ORDER BY created_at DESC",
                (buyer_user_id,),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            await conn.close()
