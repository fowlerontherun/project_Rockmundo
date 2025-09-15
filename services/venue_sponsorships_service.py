# File: backend/services/venue_sponsorships_service.py
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.models.venue_sponsorship import (
    NegotiationStage,
    SponsorshipNegotiation,
)
from config.revenue import (
    SPONSOR_IMPRESSION_RATE_CENTS,
    SPONSOR_PAYOUT_SPLIT,
)

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

@dataclass
class SponsorshipIn:
    venue_id: int
    sponsor_name: str
    sponsor_website: Optional[str] = None
    sponsor_logo_url: Optional[str] = None
    naming_pattern: Optional[str] = "{sponsor} {venue}"
    start_date: Optional[str] = None  # 'YYYY-MM-DD'
    end_date: Optional[str] = None    # 'YYYY-MM-DD'
    is_active: bool = True

class VenueSponsorshipError(Exception):
    pass

class VenueSponsorshipsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # -------- schema --------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS venue_sponsorships (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              venue_id INTEGER NOT NULL,
              sponsor_name TEXT NOT NULL,
              sponsor_website TEXT,
              sponsor_logo_url TEXT,
              naming_pattern TEXT DEFAULT "{sponsor} {venue}",
              start_date TEXT,
              end_date TEXT,
              is_active INTEGER DEFAULT 1,
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT,
              UNIQUE(venue_id)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS sponsor_ad_impressions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sponsorship_id INTEGER NOT NULL,
              impression_time TEXT DEFAULT (datetime('now')),
              user_id INTEGER,
              placement TEXT,
              event_id INTEGER,
              meta_json TEXT
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_sponsor_impr_sponsorship ON sponsor_ad_impressions(sponsorship_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_sponsor_impr_event ON sponsor_ad_impressions(event_id)")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS sponsorship_ad_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sponsorship_id INTEGER NOT NULL,
              event_type TEXT NOT NULL,
              occurred_at TEXT DEFAULT (datetime('now')),
              meta_json TEXT
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_ad_events_sponsorship ON sponsorship_ad_events(sponsorship_id)")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS venue_sponsorship_negotiations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              venue_id INTEGER NOT NULL,
              sponsor_name TEXT NOT NULL,
              terms_json TEXT NOT NULL,
              stage TEXT NOT NULL DEFAULT 'offer',
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT
            )
            """)
            conn.commit()

    # -------- helpers --------
    def _now(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def _is_within_dates(self, start: Optional[str], end: Optional[str], now_date: Optional[str] = None) -> bool:
        if not now_date:
            now_date = datetime.utcnow().strftime("%Y-%m-%d")
        if start and now_date < start:
            return False
        if end and now_date > end:
            return False
        return True

    # -------- CRUD --------
    def upsert_sponsorship(self, data: SponsorshipIn) -> int:
        # Only one row per venue; we overwrite if exists
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM venue_sponsorships WHERE venue_id = ?", (data.venue_id,))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE venue_sponsorships
                    SET sponsor_name = ?, sponsor_website = ?, sponsor_logo_url = ?, naming_pattern = ?,
                        start_date = ?, end_date = ?, is_active = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (data.sponsor_name, data.sponsor_website, data.sponsor_logo_url, data.naming_pattern,
                      data.start_date, data.end_date, int(data.is_active), int(row[0])))
                conn.commit()
                return int(row[0])
            else:
                cur.execute("""
                    INSERT INTO venue_sponsorships
                      (venue_id, sponsor_name, sponsor_website, sponsor_logo_url, naming_pattern, start_date, end_date, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (data.venue_id, data.sponsor_name, data.sponsor_website, data.sponsor_logo_url,
                      data.naming_pattern, data.start_date, data.end_date, int(data.is_active)))
                conn.commit()
                return cur.lastrowid

    def get_sponsorship(self, venue_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM venue_sponsorships WHERE venue_id = ?", (venue_id,))
            r = cur.fetchone()
            return dict(r) if r else None

    def deactivate(self, venue_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE venue_sponsorships SET is_active = 0, updated_at = datetime('now') WHERE venue_id = ?", (venue_id,))
            if cur.rowcount == 0:
                raise VenueSponsorshipError("No sponsorship row for this venue")
            conn.commit()

    def effective_branding(self, venue_id: int, venue_name: str, on_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns the branding payload to display on the site:
        - display_name (sponsored name if active & within dates; else original venue name)
        - sponsor_logo_url, sponsor_website, sponsor_name
        """
        s = self.get_sponsorship(venue_id)
        if not s:
            return {"display_name": venue_name, "sponsored": False}
        if not s["is_active"]:
            return {"display_name": venue_name, "sponsored": False}
        if not self._is_within_dates(s["start_date"], s["end_date"], on_date):
            return {"display_name": venue_name, "sponsored": False}
        pattern = s.get("naming_pattern") or "{sponsor} {venue}"
        display_name = pattern.replace("{sponsor}", s["sponsor_name"]).replace("{venue}", venue_name)
        return {
            "display_name": display_name,
            "sponsored": True,
            "sponsor_name": s["sponsor_name"],
            "sponsor_logo_url": s.get("sponsor_logo_url"),
            "sponsor_website": s.get("sponsor_website"),
            "start_date": s.get("start_date"),
            "end_date": s.get("end_date"),
        }

    # -------- negotiation --------
    def _row_to_negotiation(self, row: sqlite3.Row) -> SponsorshipNegotiation:
        return SponsorshipNegotiation(
            id=row["id"],
            venue_id=row["venue_id"],
            sponsor_name=row["sponsor_name"],
            terms=json.loads(row["terms_json"]),
            stage=NegotiationStage(row["stage"]),
        )

    def get_negotiation(self, negotiation_id: int) -> SponsorshipNegotiation:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM venue_sponsorship_negotiations WHERE id = ?",
                (negotiation_id,),
            )
            row = cur.fetchone()
            if not row:
                raise VenueSponsorshipError("Negotiation not found")
            return self._row_to_negotiation(row)

    def create_offer(
        self, venue_id: int, sponsor_name: str, terms: Dict[str, Any]
    ) -> SponsorshipNegotiation:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO venue_sponsorship_negotiations
                  (venue_id, sponsor_name, terms_json, stage)
                VALUES (?, ?, ?, ?)
                """,
                (
                    venue_id,
                    sponsor_name,
                    json.dumps(terms),
                    NegotiationStage.OFFER.value,
                ),
            )
            conn.commit()
            nid = cur.lastrowid
        return SponsorshipNegotiation(
            id=nid,
            venue_id=venue_id,
            sponsor_name=sponsor_name,
            terms=terms,
            stage=NegotiationStage.OFFER,
        )

    def counter_offer(
        self, negotiation_id: int, terms: Dict[str, Any]
    ) -> SponsorshipNegotiation:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE venue_sponsorship_negotiations
                SET terms_json = ?, stage = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    json.dumps(terms),
                    NegotiationStage.COUNTER.value,
                    negotiation_id,
                ),
            )
            if cur.rowcount == 0:
                raise VenueSponsorshipError("Negotiation not found")
            conn.commit()
        return self.get_negotiation(negotiation_id)

    def accept_offer(self, negotiation_id: int) -> SponsorshipNegotiation:
        negotiation = self.get_negotiation(negotiation_id)
        data = SponsorshipIn(
            venue_id=negotiation.venue_id,
            sponsor_name=negotiation.sponsor_name,
            sponsor_website=negotiation.terms.get("sponsor_website"),
            sponsor_logo_url=negotiation.terms.get("sponsor_logo_url"),
            naming_pattern=negotiation.terms.get("naming_pattern", "{sponsor} {venue}"),
            start_date=negotiation.terms.get("start_date"),
            end_date=negotiation.terms.get("end_date"),
            is_active=bool(negotiation.terms.get("is_active", True)),
        )
        self.upsert_sponsorship(data)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE venue_sponsorship_negotiations SET stage = ?, updated_at = datetime('now') WHERE id = ?",
                (NegotiationStage.ACCEPTED.value, negotiation_id),
            )
            if cur.rowcount == 0:
                raise VenueSponsorshipError("Negotiation not found")
            conn.commit()
        return self.get_negotiation(negotiation_id)

    # -------- Ad tracking --------
    def record_ad_event(
        self,
        sponsorship_id: int,
        event_type: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> int:
        if event_type not in ("impression", "click"):
            raise VenueSponsorshipError("event_type must be 'impression' or 'click'")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO sponsorship_ad_events (sponsorship_id, event_type, meta_json)
                VALUES (?, ?, ?)
                """,
                (sponsorship_id, event_type, json.dumps(meta) if meta else None),
            )
            conn.commit()
            return cur.lastrowid

    def record_impression(
        self,
        sponsorship_id: int,
        placement: Optional[str] = None,
        user_id: Optional[int] = None,
        event_id: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO sponsor_ad_impressions (sponsorship_id, placement, user_id, event_id, meta_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sponsorship_id, placement, user_id, event_id, json.dumps(meta) if meta else None),
            )
            cur.execute(
                """
                INSERT INTO sponsorship_ad_events (sponsorship_id, event_type, meta_json)
                VALUES (?, 'impression', ?)
                """,
                (sponsorship_id, json.dumps(meta) if meta else None),
            )
            conn.commit()
            return cur.lastrowid

    def list_impressions(self, sponsorship_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM sponsor_ad_impressions
                WHERE sponsorship_id = ?
                ORDER BY impression_time DESC
                LIMIT ?
            """, (sponsorship_id, limit))
            return [dict(r) for r in cur.fetchall()]

    def get_ad_rollup(self, sponsorship_id: int) -> Dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT event_type, COUNT(*) as cnt
                FROM sponsorship_ad_events
                WHERE sponsorship_id = ?
                GROUP BY event_type
                """,
                (sponsorship_id,),
            )
            rows = cur.fetchall()
        out = {"impressions": 0, "clicks": 0}
        for event_type, cnt in rows:
            if event_type == "impression":
                out["impressions"] = int(cnt)
            elif event_type == "click":
                out["clicks"] = int(cnt)
        return out

    def calculate_payout(self, sponsorship_id: int) -> Dict[str, int]:
        rollup = self.get_ad_rollup(sponsorship_id)
        impressions = rollup.get("impressions", 0)
        gross = impressions * SPONSOR_IMPRESSION_RATE_CENTS
        venue_share = gross * SPONSOR_PAYOUT_SPLIT.get("venue", 0) // 100
        platform_share = gross - venue_share
        return {
            "impressions": impressions,
            "gross_cents": gross,
            "venue_cents": venue_share,
            "platform_cents": platform_share,
        }
