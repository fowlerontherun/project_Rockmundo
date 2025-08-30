# File: backend/services/merch_service.py
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.models.merch import CartItem, ProductIn, SKUIn
from services.economy_service import EconomyError, EconomyService
from services.payment_service import PaymentError, PaymentService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

class MerchError(Exception):
    pass

class MerchService:
    def __init__(
        self,
        db_path: Optional[str] = None,
        economy: EconomyService | None = None,
        payments: PaymentService | None = None,
    ):
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(db_path=self.db_path)
        self.payments = payments
        self.economy.ensure_schema()

    # -------- schema --------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS merch_products (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              band_id INTEGER,
              name TEXT NOT NULL,
              description TEXT,
              category TEXT NOT NULL,
              image_url TEXT,
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS merch_skus (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              product_id INTEGER NOT NULL,
              option_size TEXT,
              option_color TEXT,
              price_cents INTEGER NOT NULL,
              currency TEXT DEFAULT 'USD',
              stock_qty INTEGER NOT NULL DEFAULT 0,
              barcode TEXT,
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT,
              FOREIGN KEY(product_id) REFERENCES merch_products(id)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS merch_orders (
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
            cur.execute("""
            CREATE TABLE IF NOT EXISTS merch_order_items (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              order_id INTEGER NOT NULL,
              sku_id INTEGER NOT NULL,
              unit_price_cents INTEGER NOT NULL,
              qty INTEGER NOT NULL,
              refunded_qty INTEGER NOT NULL DEFAULT 0,
              created_at TEXT DEFAULT (datetime('now')),
              FOREIGN KEY(order_id) REFERENCES merch_orders(id),
              FOREIGN KEY(sku_id) REFERENCES merch_skus(id)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS merch_refunds (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              order_id INTEGER NOT NULL,
              amount_cents INTEGER NOT NULL,
              reason TEXT,
              created_at TEXT DEFAULT (datetime('now')),
              FOREIGN KEY(order_id) REFERENCES merch_orders(id)
            )
            """)
            # Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS ix_merch_skus_product ON merch_skus(product_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_merch_items_order ON merch_order_items(order_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_merch_items_sku ON merch_order_items(sku_id)")
            conn.commit()

    # -------- products --------
    def create_product(self, payload: ProductIn) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO merch_products (band_id, name, description, category, image_url, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (payload.band_id, payload.name, payload.description, payload.category, payload.image_url, int(payload.is_active)),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def list_products(self, only_active: bool = True, category: Optional[str] = None, band_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            q = "SELECT * FROM merch_products"
            where: list[str] = []
            vals: list[Any] = []
            if only_active:
                where.append("is_active = 1")
            if category:
                where.append("category = ?")
                vals.append(category)
            if band_id is not None:
                where.append("band_id = ?")
                vals.append(band_id)
            if where:
                q += " WHERE " + " AND ".join(where)
            q += " ORDER BY created_at DESC"
            cur.execute(q, tuple(vals))
            return [dict(r) for r in cur.fetchall()]

    def update_product(self, product_id: int, **fields) -> None:
        if not fields:
            return
        allowed = ("name","description","category","image_url","is_active","band_id")
        cols, vals = [], []
        for k in allowed:
            if k in fields:
                cols.append(f"{k} = ?")
                vals.append(fields[k])
        if not cols:
            return
        vals.append(product_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE merch_products SET {', '.join(cols)}, updated_at=datetime('now') WHERE id = ?", vals)
            if cur.rowcount == 0:
                raise MerchError("Product not found")
            conn.commit()

    # -------- skus --------
    def create_sku(self, payload: SKUIn) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO merch_skus (product_id, option_size, option_color, price_cents, currency, stock_qty, barcode, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.product_id,
                    payload.option_size,
                    payload.option_color,
                    payload.price_cents,
                    payload.currency,
                    payload.stock_qty,
                    payload.barcode,
                    int(payload.is_active),
                ),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def list_skus(self, product_id: int, only_active: bool = True) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            q = "SELECT * FROM merch_skus WHERE product_id = ?"
            vals = [product_id]
            if only_active:
                q += " AND is_active = 1"
            q += " ORDER BY price_cents ASC"
            cur.execute(q, tuple(vals))
            return [dict(r) for r in cur.fetchall()]

    def update_sku(self, sku_id: int, **fields) -> None:
        if not fields:
            return
        allowed = ("option_size","option_color","price_cents","currency","stock_qty","barcode","is_active")
        cols, vals = [], []
        for k in allowed:
            if k in fields:
                cols.append(f"{k} = ?")
                vals.append(fields[k])
        if not cols:
            return
        vals.append(sku_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE merch_skus SET {', '.join(cols)}, updated_at=datetime('now') WHERE id = ?", vals)
            if cur.rowcount == 0:
                raise MerchError("SKU not found")
            conn.commit()

    # -------- stock helpers --------
    def _sku_remaining(self, cur, sku_id: int) -> int:
        cur.execute("SELECT stock_qty FROM merch_skus WHERE id = ?", (sku_id,))
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0

    # -------- orders --------
    def purchase(self, buyer_user_id: int, items: List[Dict[str, int]], shipping_address: Optional[str] = None) -> int:
        norm = [CartItem(int(x["sku_id"]), int(x["qty"])) for x in items if int(x.get("qty", 0)) > 0]
        if not norm:
            raise MerchError("No items specified")
        band_totals: Dict[int, int] = {}
        total_cents = 0
        currency = "USD"
        # gather sku info first
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            for it in norm:
                cur.execute(
                    """
                    SELECT s.*, p.band_id FROM merch_skus s
                    JOIN merch_products p ON p.id = s.product_id
                    WHERE s.id = ? AND s.is_active = 1
                    """,
                    (it.sku_id,),
                )
                sku = cur.fetchone()
                if not sku:
                    raise MerchError("SKU not found or inactive")
                remaining = int(sku["stock_qty"])
                if remaining < it.qty:
                    raise MerchError(f"Insufficient stock for SKU {it.sku_id}")
                total_cents += int(sku["price_cents"]) * it.qty
                currency = sku["currency"] or currency
                band_id = sku["band_id"]
                if band_id is not None:
                    band_totals[band_id] = band_totals.get(band_id, 0) + int(sku["price_cents"]) * it.qty
        if self.payments:
            try:
                pid = self.payments.initiate_purchase(buyer_user_id, total_cents, currency)
                self.payments.verify_callback(pid)
            except PaymentError as e:
                raise MerchError(str(e))
        try:
            self.economy.withdraw(buyer_user_id, total_cents, currency)
        except EconomyError as e:
            raise MerchError(str(e))
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")
                cur.execute(
                    """
                    INSERT INTO merch_orders (buyer_user_id, total_cents, currency, status, shipping_address)
                    VALUES (?, ?, ?, 'confirmed', ?)
                    """,
                    (buyer_user_id, total_cents, currency, shipping_address),
                )
                order_id = int(cur.lastrowid or 0)
                for it in norm:
                    cur.execute("SELECT price_cents FROM merch_skus WHERE id = ?", (it.sku_id,))
                    price = int(cur.fetchone()[0])
                    cur.execute(
                        """
                        INSERT INTO merch_order_items (order_id, sku_id, unit_price_cents, qty)
                        VALUES (?, ?, ?, ?)
                        """,
                        (order_id, it.sku_id, price, it.qty),
                    )
                    cur.execute("UPDATE merch_skus SET stock_qty = stock_qty - ? WHERE id = ?", (it.qty, it.sku_id))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        for band_id, amt in band_totals.items():
            try:
                self.economy.deposit(band_id, amt, currency)
            except EconomyError:
                pass
        return order_id
    def refund_order(self, order_id: int, reason: str = "") -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM merch_orders WHERE id = ?", (order_id,))
            order = cur.fetchone()
            if not order:
                raise MerchError("Order not found")
            if order["status"] == "refunded":
                raise MerchError("Order already refunded")

            cur.execute("""
                SELECT SUM(unit_price_cents * (qty - refunded_qty)) AS refundable,
                       SUM(qty - refunded_qty) AS units_to_return
                FROM merch_order_items
                WHERE order_id = ?
            """, (order_id,))
            row = cur.fetchone()
            refundable = int(row["refundable"] or 0)
            units_to_return = int(row["units_to_return"] or 0)
            if refundable <= 0:
                raise MerchError("Nothing to refund")

            try:
                cur.execute("BEGIN IMMEDIATE")
                cur.execute("UPDATE merch_orders SET status='refunded', updated_at=datetime('now') WHERE id = ?", (order_id,))
                cur.execute("UPDATE merch_order_items SET refunded_qty = qty WHERE order_id = ?", (order_id,))
                # restore stock
                cur.execute("SELECT sku_id, qty FROM merch_order_items WHERE order_id = ?", (order_id,))
                for r in cur.fetchall():
                    cur.execute("UPDATE merch_skus SET stock_qty = stock_qty + ? WHERE id = ?", (int(r["qty"]), int(r["sku_id"])))
                # record refund
                cur.execute(
                    """
                    INSERT INTO merch_refunds (order_id, amount_cents, reason)
                    VALUES (?, ?, ?)
                    """,
                    (order_id, refundable, reason),
                )
                self.economy.deposit(order["buyer_user_id"], refundable, currency=order["currency"])
                conn.commit()
                return {"order_id": order_id, "refunded_cents": refundable, "units_returned": units_to_return}
            except Exception:
                conn.rollback()
                raise

    # -------- queries --------
    def get_order(self, order_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM merch_orders WHERE id = ?", (order_id,))
            o = cur.fetchone()
            if not o:
                raise MerchError("Order not found")
            cur.execute("""
                SELECT oi.*, p.name as product_name, s.option_size, s.option_color
                FROM merch_order_items oi
                JOIN merch_skus s ON s.id = oi.sku_id
                JOIN merch_products p ON p.id = s.product_id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = [dict(r) for r in cur.fetchall()]
            out = dict(o)
            out["items"] = items
            return out

    def list_orders_for_user(self, buyer_user_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM merch_orders WHERE buyer_user_id = ? ORDER BY created_at DESC", (buyer_user_id,))
            return [dict(r) for r in cur.fetchall()]
