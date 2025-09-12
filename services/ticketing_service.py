# File: backend/services/ticketing_service.py
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.economy_service import EconomyError, EconomyService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

@dataclass
class TicketItem:
    ticket_type_id: int
    qty: int

class TicketingError(Exception):
    pass

class TicketingService:
    def __init__(self, db_path: Optional[str] = None, economy: EconomyService | None = None):
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(db_path=self.db_path)
        self.economy.ensure_schema()

    # ---------------- Schema ----------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ticket_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                total_qty INTEGER NOT NULL,
                max_per_user INTEGER DEFAULT 10,
                sales_start TEXT,
                sales_end TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ticket_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                total_cents INTEGER NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ticket_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                ticket_type_id INTEGER NOT NULL,
                unit_price_cents INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                refunded_qty INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(order_id) REFERENCES ticket_orders(id),
                FOREIGN KEY(ticket_type_id) REFERENCES ticket_types(id)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ticket_refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount_cents INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(order_id) REFERENCES ticket_orders(id)
            )
            """)
            cur.execute("""CREATE INDEX IF NOT EXISTS ix_ticket_types_event ON ticket_types(event_id)""")
            cur.execute("""CREATE INDEX IF NOT EXISTS ix_orders_event ON ticket_orders(event_id)""")
            cur.execute("""CREATE INDEX IF NOT EXISTS ix_order_items_order ON ticket_order_items(order_id)""")
            cur.execute("""CREATE INDEX IF NOT EXISTS ix_order_items_type ON ticket_order_items(ticket_type_id)""")
            conn.commit()

    # ---------------- Helpers ----------------
    def _now(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def _get_type(self, cur, ticket_type_id: int) -> Optional[sqlite3.Row]:
        cur.execute("SELECT * FROM ticket_types WHERE id = ?", (ticket_type_id,))
        return cur.fetchone()

    def _remaining_for_type(self, cur, ticket_type_id: int) -> int:
        cur.execute("""
            SELECT
              tt.total_qty
              - IFNULL((
                SELECT SUM(qty - refunded_qty) FROM ticket_order_items oi
                JOIN ticket_orders o ON o.id = oi.order_id
                WHERE oi.ticket_type_id = tt.id AND o.status IN ('confirmed','pending')
              ), 0) AS remaining
            FROM ticket_types tt
            WHERE tt.id = ?
        """, (ticket_type_id,))
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0

    def _user_qty_for_event(self, cur, user_id: int, event_id: int) -> int:
        cur.execute("""
            SELECT IFNULL(SUM(oi.qty - oi.refunded_qty), 0)
            FROM ticket_order_items oi
            JOIN ticket_orders o ON o.id = oi.order_id
            JOIN ticket_types tt ON tt.id = oi.ticket_type_id
            WHERE o.user_id = ? AND o.event_id = ? AND o.status IN ('confirmed','pending')
        """, (user_id, event_id))
        row = cur.fetchone()
        return int(row[0] or 0)

    def _sum_items_price(self, cur, items: List[TicketItem]) -> int:
        total = 0
        for it in items:
            cur.execute("SELECT price_cents, currency FROM ticket_types WHERE id = ?", (it.ticket_type_id,))
            row = cur.fetchone()
            if not row:
                raise TicketingError("Ticket type not found")
            price_cents = int(row[0])
            total += price_cents * int(it.qty)
        return total

    # ---------------- Ticket Types ----------------
    def create_ticket_type(
        self,
        event_id: int,
        name: str,
        price_cents: int,
        total_qty: int,
        currency: str = "USD",
        max_per_user: int = 10,
        sales_start: Optional[str] = None,
        sales_end: Optional[str] = None,
        is_active: bool = True,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO ticket_types (event_id, name, price_cents, currency, total_qty, max_per_user, sales_start, sales_end, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, name, price_cents, currency, total_qty, max_per_user, sales_start, sales_end, int(is_active)),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def list_ticket_types(self, event_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM ticket_types WHERE event_id = ? ORDER BY price_cents ASC", (event_id,))
            rows = cur.fetchall()
            out = []
            for r in rows:
                remaining = self._remaining_for_type(cur, r["id"])
                d = dict(r)
                d["remaining"] = remaining
                out.append(d)
            return out

    def update_ticket_type(self, ticket_type_id: int, **fields) -> None:
        if not fields:
            return
        cols = []
        vals = []
        for k in ("name","price_cents","currency","total_qty","max_per_user","sales_start","sales_end","is_active"):
            if k in fields:
                cols.append(f"{k} = ?")
                vals.append(int(fields[k]) if k in ("price_cents","total_qty","max_per_user","is_active") else fields[k])
        if not cols:
            return
        vals.append(ticket_type_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE ticket_types SET {', '.join(cols)}, updated_at = datetime('now') WHERE id = ?", vals)
            conn.commit()

    # ---------------- Purchases ----------------
    def purchase_tickets(self, user_id: int, event_id: int, items: List[Dict[str, int]]) -> int:
        norm_items = [TicketItem(int(x["ticket_type_id"]), int(x["qty"])) for x in items if int(x.get("qty", 0)) > 0]
        if not norm_items:
            raise TicketingError("No ticket items specified")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")

                total_for_user_existing = self._user_qty_for_event(cur, user_id, event_id)
                total_new_qty = 0
                now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                cap_per_user = None
                for it in norm_items:
                    cur.execute("SELECT * FROM ticket_types WHERE id = ?", (it.ticket_type_id,))
                    tt = cur.fetchone()
                    if not tt:
                        raise TicketingError("Ticket type not found")
                    if int(tt["event_id"]) != int(event_id):
                        raise TicketingError("Ticket type does not belong to this event")
                    if int(tt["is_active"]) != 1:
                        raise TicketingError("Ticket type is not active")

                    ss = tt["sales_start"]
                    se = tt["sales_end"]
                    if ss and now_iso < ss:
                        raise TicketingError("Sales have not started for this ticket type")
                    if se and now_iso > se:
                        raise TicketingError("Sales have ended for this ticket type")

                    remaining = self._remaining_for_type(cur, it.ticket_type_id)
                    if remaining < it.qty:
                        raise TicketingError(f"Not enough tickets remaining for type {tt['name']}")

                    total_new_qty += it.qty
                    cap = int(tt["max_per_user"] or 10)
                    cap_per_user = cap if cap_per_user is None else min(cap_per_user, cap)

                if total_for_user_existing + total_new_qty > (cap_per_user or 10):
                    raise TicketingError("Per-user ticket limit exceeded for this event")

                total_cents = self._sum_items_price(cur, norm_items)
                currency = "USD"
                cur.execute("SELECT currency FROM ticket_types WHERE id = ?", (norm_items[0].ticket_type_id,))
                row = cur.fetchone()
                if row and row["currency"]:
                    currency = row["currency"]

                try:
                    self.economy.withdraw(user_id, total_cents, currency)
                except EconomyError as e:
                    raise TicketingError(str(e))

                cur.execute(
                    """
                    INSERT INTO ticket_orders (user_id, event_id, total_cents, currency, status)
                    VALUES (?, ?, ?, ?, 'confirmed')
                    """,
                    (user_id, event_id, total_cents, currency),
                )
                order_id = int(cur.lastrowid or 0)

                for it in norm_items:
                    cur.execute("SELECT price_cents FROM ticket_types WHERE id = ?", (it.ticket_type_id,))
                    price = int(cur.fetchone()[0])
                    cur.execute("""
                        INSERT INTO ticket_order_items (order_id, ticket_type_id, unit_price_cents, qty)
                        VALUES (?, ?, ?, ?)
                    """, (order_id, it.ticket_type_id, price, it.qty))

                conn.commit()
                return order_id
            except Exception:
                conn.rollback()
                raise

    # ---------------- Refunds ----------------
    def refund_order(self, order_id: int, reason: str = "") -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM ticket_orders WHERE id = ?", (order_id,))
            order = cur.fetchone()
            if not order:
                raise TicketingError("Order not found")
            if order["status"] == "refunded":
                raise TicketingError("Order is already refunded")

            cur.execute(
                """
                SELECT SUM(unit_price_cents * (qty - refunded_qty)) AS refundable
                FROM ticket_order_items
                WHERE order_id = ?
                """,
                (order_id,),
            )
            row = cur.fetchone()
            refundable = int(row["refundable"] or 0)
            if refundable <= 0:
                raise TicketingError("Nothing to refund")

            try:
                cur.execute("BEGIN IMMEDIATE")
                cur.execute(
                    "UPDATE ticket_orders SET status = 'refunded', updated_at = datetime('now') WHERE id = ?",
                    (order_id,),
                )
                cur.execute(
                    "UPDATE ticket_order_items SET refunded_qty = qty WHERE order_id = ?",
                    (order_id,),
                )
                cur.execute(
                    """
                    INSERT INTO ticket_refunds (order_id, amount_cents, reason)
                    VALUES (?, ?, ?)
                    """,
                    (order_id, refundable, reason),
                )
                self.economy.deposit(order["user_id"], refundable, currency=order["currency"])
                conn.commit()
                return {"order_id": order_id, "refunded_cents": refundable}
            except Exception:
                conn.rollback()
                raise

    # ---------------- Queries ----------------
    def get_order(self, order_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM ticket_orders WHERE id = ?", (order_id,))
            o = cur.fetchone()
            if not o:
                raise TicketingError("Order not found")
            cur.execute("""
                SELECT oi.*, tt.name AS ticket_name
                FROM ticket_order_items oi
                JOIN ticket_types tt ON tt.id = oi.ticket_type_id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = [dict(r) for r in cur.fetchall()]
            data = dict(o)
            data["items"] = items
            return data

    def list_orders_for_event(self, event_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM ticket_orders WHERE event_id = ? ORDER BY created_at DESC", (event_id,))
            return [dict(r) for r in cur.fetchall()]

    def remaining_by_type(self, ticket_type_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            return self._remaining_for_type(cur, ticket_type_id)
