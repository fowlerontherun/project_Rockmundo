# File: backend/services/gifting_service.py
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.services.xp_reward_service import xp_reward_service

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

class GiftingError(Exception):
    pass

@dataclass
class DigitalGiftIn:
    sender_user_id: int
    recipient_user_id: int
    work_type: str   # 'song' | 'album'
    work_id: int
    price_cents: int
    currency: str = "USD"
    message: Optional[str] = None

@dataclass
class TicketGiftItem:
    ticket_type_id: int
    qty: int

@dataclass
class TicketGiftIn:
    sender_user_id: int
    recipient_user_id: int
    event_id: int
    items: List[TicketGiftItem]
    currency: str = "USD"
    message: Optional[str] = None

class GiftingService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # ---------- schema ----------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_user_id INTEGER NOT NULL,
                recipient_user_id INTEGER NOT NULL,
                category TEXT NOT NULL,           -- 'digital' | 'ticket'
                status TEXT NOT NULL DEFAULT 'delivered', -- 'pending'|'delivered'|'cancelled'
                message TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS gift_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gift_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,          -- 'song'|'album'|'ticket_type'
                item_id INTEGER NOT NULL,
                qty INTEGER NOT NULL DEFAULT 1,
                meta_json TEXT,
                FOREIGN KEY(gift_id) REFERENCES gifts(id)
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_gifts_recipient ON gifts(recipient_user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_gifts_sender ON gifts(sender_user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_gift_items_gift ON gift_items(gift_id)")
            conn.commit()

    # ---------- helpers ----------
    def _table_exists(self, cur, name: str) -> bool:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    def _notify(self, cur, user_id: int, title: str, body: str, link: Optional[str] = None) -> None:
        # Best-effort notification if notifications table exists
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'")
            if cur.fetchone():
                cur.execute("""
                    INSERT INTO notifications (user_id, type, title, body, link)
                    VALUES (?, 'gift', ?, ?, ?)
                """, (user_id, title, body, link))
        except Exception:
            # ignore
            pass

    # ---------- digital gifting ----------
    def gift_digital(self, data: DigitalGiftIn) -> int:
        work_type = data.work_type.lower()
        if work_type not in ("song","album"):
            raise GiftingError("work_type must be 'song' or 'album'")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()
            try:
                cur.execute("BEGIN IMMEDIATE")
                # Create gift envelope
                cur.execute("""
                    INSERT INTO gifts (sender_user_id, recipient_user_id, category, status, message)
                    VALUES (?, ?, 'digital', 'delivered', ?)
                """, (data.sender_user_id, data.recipient_user_id, data.message))
                gift_id = cur.lastrowid
                cur.execute("""
                    INSERT INTO gift_items (gift_id, item_type, item_id, qty, meta_json)
                    VALUES (?, ?, ?, 1, ?)
                """, (gift_id, work_type, data.work_id, json.dumps({"currency": data.currency, "price_cents": data.price_cents})))

                # Record a digital sale attributed to the sender as buyer
                if self._table_exists(cur, "digital_sales"):
                    cur.execute("""
                        INSERT INTO digital_sales (buyer_user_id, work_type, work_id, price_cents, currency, source)
                        VALUES (?, ?, ?, ?, ?, 'gift')
                    """, (data.sender_user_id, work_type, data.work_id, data.price_cents, data.currency))

                # Optional entitlement table (if exists): grant to recipient
                if self._table_exists(cur, "digital_entitlements"):
                    cur.execute("""
                        INSERT INTO digital_entitlements (user_id, work_type, work_id, granted_by, source)
                        VALUES (?, ?, ?, ?, 'gift')
                        ON CONFLICT(user_id, work_type, work_id) DO NOTHING
                    """, (data.recipient_user_id, work_type, data.work_id, data.sender_user_id))

                # Best-effort notification
                self._notify(cur, data.recipient_user_id, "You've received a gift!", f"A {work_type} was gifted to you.", None)

                conn.commit()
                # Secretly reward new players with a bit of XP
                xp_reward_service.grant_hidden_xp(data.recipient_user_id, reason="gift")
                return gift_id
            except Exception:
                conn.rollback()
                raise

    # ---------- ticket gifting ----------
    def gift_tickets(self, data: TicketGiftIn) -> int:
        if not data.items:
            raise GiftingError("No ticket items specified")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()
            try:
                cur.execute("BEGIN IMMEDIATE")
                # Create gift envelope
                cur.execute("""
                    INSERT INTO gifts (sender_user_id, recipient_user_id, category, status, message)
                    VALUES (?, ?, 'ticket', 'delivered', ?)
                """, (data.sender_user_id, data.recipient_user_id, data.message))
                gift_id = cur.lastrowid

                total_cents = 0
                # Check ticket tables exist
                needed = ["ticket_orders","ticket_order_items","ticket_types"]
                if not all(self._table_exists(cur, t) for t in needed):
                    raise GiftingError("Ticketing tables missing; cannot gift tickets")

                # Price items & create recipient order
                for it in data.items:
                    cur.execute("SELECT price_cents FROM ticket_types WHERE id = ? AND event_id = ?", (it.ticket_type_id, data.event_id))
                    row = cur.fetchone()
                    if not row:
                        raise GiftingError(f"Ticket type {it.ticket_type_id} not found for event {data.event_id}")
                    price = int(row["price_cents"])
                    if it.qty <= 0:
                        raise GiftingError("qty must be > 0")
                    total_cents += price * it.qty

                # Create a confirmed order for the recipient
                cur.execute("""
                    INSERT INTO ticket_orders (event_id, buyer_user_id, total_cents, currency, status)
                    VALUES (?, ?, ?, ?, 'confirmed')
                """, (data.event_id, data.recipient_user_id, total_cents, data.currency))
                order_id = cur.lastrowid

                for it in data.items:
                    cur.execute("SELECT price_cents FROM ticket_types WHERE id = ?", (it.ticket_type_id,))
                    price = int(cur.fetchone()["price_cents"])
                    cur.execute("""
                        INSERT INTO ticket_order_items (order_id, ticket_type_id, qty, unit_price_cents)
                        VALUES (?, ?, ?, ?)
                    """, (order_id, it.ticket_type_id, it.qty, price))

                    # Add to gift items list
                    cur.execute("""
                        INSERT INTO gift_items (gift_id, item_type, item_id, qty, meta_json)
                        VALUES (?, 'ticket_type', ?, ?, ?)
                    """, (gift_id, it.ticket_type_id, it.qty, json.dumps({"event_id": data.event_id, "unit_price_cents": price})))

                # Best-effort notification
                self._notify(cur, data.recipient_user_id, "You've received tickets!", f"Gifted tickets for event {data.event_id}.", None)

                conn.commit()
                xp_reward_service.grant_hidden_xp(data.recipient_user_id, reason="gift")
                return gift_id
            except Exception:
                conn.rollback()
                raise

    # ---------- queries ----------
    def list_inbox(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM gifts
                WHERE recipient_user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            gifts = [dict(r) for r in cur.fetchall()]
            for g in gifts:
                cur.execute("SELECT item_type, item_id, qty, meta_json FROM gift_items WHERE gift_id = ?", (g["id"],))
                items = []
                for it in cur.fetchall():
                    items.append({
                        "item_type": it["item_type"],
                        "item_id": it["item_id"],
                        "qty": it["qty"],
                        "meta": json.loads(it["meta_json"]) if it["meta_json"] else None
                    })
                g["items"] = items
            return gifts

    def list_sent(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM gifts
                WHERE sender_user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            gifts = [dict(r) for r in cur.fetchall()]
            for g in gifts:
                cur.execute("SELECT item_type, item_id, qty, meta_json FROM gift_items WHERE gift_id = ?", (g["id"],))
                items = []
                for it in cur.fetchall():
                    items.append({
                        "item_type": it["item_type"],
                        "item_id": it["item_id"],
                        "qty": it["qty"],
                        "meta": json.loads(it["meta_json"]) if it["meta_json"] else None
                    })
                g["items"] = items
            return gifts
