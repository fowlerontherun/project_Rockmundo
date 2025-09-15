from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from services.economy_service import EconomyService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class CrowdfundingError(Exception):
    pass


class CrowdfundingService:
    """Service managing crowdfunding campaigns and pledges."""

    def __init__(self, economy: Optional[EconomyService] = None, db_path: str | None = None):
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(db_path=self.db_path)
        try:
            self.economy.ensure_schema()
        except Exception:
            pass

    # ------------------------------------------------------------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER NOT NULL,
                    goal_cents INTEGER NOT NULL,
                    pledged_cents INTEGER NOT NULL DEFAULT 0,
                    completed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS pledges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    backer_id INTEGER NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    pledged_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS payout_schedules (
                    campaign_id INTEGER PRIMARY KEY,
                    creator_share REAL NOT NULL,
                    backer_share REAL NOT NULL,
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    def create_campaign(
        self,
        creator_id: int,
        goal_cents: int,
        creator_share: float = 0.8,
        backer_share: float = 0.2,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO campaigns(creator_id, goal_cents, created_at) VALUES (?, ?, datetime('now'))",
                (creator_id, goal_cents),
            )
            cid = int(cur.lastrowid)
            cur.execute(
                "INSERT INTO payout_schedules(campaign_id, creator_share, backer_share) VALUES (?,?,?)",
                (cid, creator_share, backer_share),
            )
            conn.commit()
        return cid

    # ------------------------------------------------------------------
    def pledge(self, campaign_id: int, backer_id: int, amount_cents: int) -> int:
        self.economy.withdraw(backer_id, amount_cents)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO pledges(campaign_id, backer_id, amount_cents, pledged_at) VALUES (?, ?, ?, datetime('now'))",
                (campaign_id, backer_id, amount_cents),
            )
            pid = int(cur.lastrowid)
            cur.execute(
                "UPDATE campaigns SET pledged_cents = pledged_cents + ? WHERE id = ?",
                (amount_cents, campaign_id),
            )
            conn.commit()
        return pid

    # ------------------------------------------------------------------
    def complete_campaign(self, campaign_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT creator_id, goal_cents, pledged_cents, completed FROM campaigns WHERE id = ?",
                (campaign_id,),
            )
            row = cur.fetchone()
            if not row:
                raise CrowdfundingError("campaign_not_found")
            creator_id, goal_cents, pledged_cents, completed = row
            if completed:
                raise CrowdfundingError("campaign_already_completed")
            if pledged_cents < goal_cents:
                raise CrowdfundingError("goal_not_met")
            cur.execute("SELECT creator_share, backer_share FROM payout_schedules WHERE campaign_id=?", (campaign_id,))
            ps_row = cur.fetchone()
            creator_share, backer_share = ps_row if ps_row else (0.8, 0.2)
            cur.execute("SELECT backer_id, amount_cents FROM pledges WHERE campaign_id=?", (campaign_id,))
            pledges = cur.fetchall()
            cur.execute("UPDATE campaigns SET completed = 1 WHERE id = ?", (campaign_id,))
            conn.commit()

        total = pledged_cents
        creator_amount = int(total * creator_share)
        self.economy.deposit(creator_id, creator_amount)
        for backer_id, amt in pledges:
            share = int(amt * backer_share)
            if share:
                self.economy.deposit(backer_id, share)
