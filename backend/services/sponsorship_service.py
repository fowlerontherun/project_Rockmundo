# File: backend/services/sponsorship_service.py
import aiosqlite
from typing import Optional, Dict, Any, List
from datetime import date

from backend.config.revenue import (
    SPONSOR_IMPRESSION_RATE_CENTS,
    SPONSOR_PAYOUT_SPLIT,
)

def _display_name(venue_name: str, sponsor_name: Optional[str], fmt: str) -> str:
    if not sponsor_name:
        return venue_name
    safe_fmt = fmt or "{sponsor} {venue}"
    return safe_fmt.replace("{venue}", venue_name).replace("{sponsor}", sponsor_name)

class SponsorshipService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    # ---------- Sponsors ----------
    async def create_sponsor(self, data: Dict[str, Any]) -> int:
        async with (await aiosqlite.connect(self.db_path)) as db:
            cur = await db.execute(
                """
                INSERT INTO sponsors (name, website_url, logo_url, contact_email, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data.get("name"),
                    data.get("website_url"),
                    data.get("logo_url"),
                    data.get("contact_email"),
                    data.get("notes"),
                ),
            )
            await db.commit()
            return cur.lastrowid

    async def list_sponsors(self) -> List[Dict[str, Any]]:
        async with (await aiosqlite.connect(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM sponsors ORDER BY name ASC")
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def update_sponsor(self, sponsor_id: int, data: Dict[str, Any]) -> None:
        fields, values = [], []
        for k in ("name", "website_url", "logo_url", "contact_email", "notes"):
            if k in data:
                fields.append(f"{k} = ?")
                values.append(data[k])
        if not fields:
            return
        values.append(sponsor_id)
        async with (await aiosqlite.connect(self.db_path)) as db:
            await db.execute(
                f"UPDATE sponsors SET {', '.join(fields)}, updated_at=datetime('now') WHERE id = ?",
                values,
            )
            await db.commit()

    async def delete_sponsor(self, sponsor_id: int) -> None:
        async with (await aiosqlite.connect(self.db_path)) as db:
            await db.execute("DELETE FROM sponsors WHERE id = ?", (sponsor_id,))
            await db.commit()

    # ---------- Venue Sponsorships ----------
    async def create_venue_sponsorship(self, data: Dict[str, Any]) -> int:
        async with (await aiosqlite.connect(self.db_path)) as db:
            cur = await db.execute(
                """
                INSERT INTO venue_sponsorships (
                    venue_id, sponsor_id, start_date, end_date, is_active,
                    naming_format, show_logo, show_website,
                    revenue_model, revenue_cents_per_unit, fixed_fee_cents, currency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["venue_id"],
                    data["sponsor_id"],
                    data["start_date"],
                    data.get("end_date"),
                    int(data.get("is_active", 1)),
                    data.get("naming_format", "{sponsor} {venue}"),
                    int(data.get("show_logo", 1)),
                    int(data.get("show_website", 1)),
                    data.get("revenue_model", "CPM"),
                    data.get("revenue_cents_per_unit"),
                    data.get("fixed_fee_cents"),
                    data.get("currency", "USD"),
                ),
            )
            await db.commit()
            return cur.lastrowid

    async def list_venue_sponsorships(self, venue_id: Optional[int] = None, active_only: bool = False) -> List[Dict[str, Any]]:
        query = """
            SELECT vs.*, s.name AS sponsor_name, s.website_url AS sponsor_website, s.logo_url AS sponsor_logo
            FROM venue_sponsorships vs
            JOIN sponsors s ON s.id = vs.sponsor_id
        """
        where, params = [], []
        if venue_id is not None:
            where.append("vs.venue_id = ?")
            params.append(venue_id)
        if active_only:
            where.append("vs.is_active = 1 AND date(vs.start_date) <= date('now') AND (vs.end_date IS NULL OR date(vs.end_date) >= date('now'))")
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY vs.start_date DESC"
        async with (await aiosqlite.connect(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(query, params)
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def update_venue_sponsorship(self, sponsorship_id: int, data: Dict[str, Any]) -> None:
        fields, values = [], []
        updatable = [
            "start_date","end_date","is_active","naming_format","show_logo","show_website",
            "revenue_model","revenue_cents_per_unit","fixed_fee_cents","currency","sponsor_id","venue_id"
        ]
        for k in updatable:
            if k in data:
                if k in ("is_active","show_logo","show_website") and isinstance(data[k], bool):
                    fields.append(f"{k} = ?")
                    values.append(int(data[k]))
                else:
                    fields.append(f"{k} = ?")
                    values.append(data[k])
        if not fields:
            return
        values.append(sponsorship_id)
        async with (await aiosqlite.connect(self.db_path)) as db:
            await db.execute(
                f"UPDATE venue_sponsorships SET {', '.join(fields)}, updated_at=datetime('now') WHERE id = ?",
                values,
            )
            await db.commit()

    async def end_venue_sponsorship(self, sponsorship_id: int, end_date: Optional[str] = None) -> None:
        endDate = end_date or date.today().isoformat()
        async with (await aiosqlite.connect(self.db_path)) as db:
            await db.execute(
                """
                UPDATE venue_sponsorships
                   SET end_date = ?, is_active = 0, updated_at = datetime('now')
                 WHERE id = ?
                """,
                (endDate, sponsorship_id),
            )
            await db.commit()

    # ---------- Computed Venue Display ----------
    async def get_venue_with_sponsorship(self, venue_id: int) -> Dict[str, Any]:
        async with (await aiosqlite.connect(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM venues WHERE id = ?", (venue_id,))
            venue = await cur.fetchone()
            if not venue:
                raise ValueError("Venue not found")

            cur = await db.execute(
                """
                SELECT vs.*, s.name AS sponsor_name, s.website_url AS sponsor_website, s.logo_url AS sponsor_logo
                FROM v_current_venue_sponsorship vs
                JOIN sponsors s ON s.id = vs.sponsor_id
                WHERE vs.venue_id = ?
                ORDER BY vs.start_date DESC
                LIMIT 1
                """,
                (venue_id,),
            )
            sp = await cur.fetchone()

            sponsor_block = None
            display_name = venue["name"]
            if sp:
                display_name = _display_name(venue["name"], sp["sponsor_name"], sp["naming_format"])
                sponsor_block = {
                    "sponsor_id": sp["sponsor_id"],
                    "name": sp["sponsor_name"],
                    "website_url": sp["sponsor_website"] if sp["show_website"] else None,
                    "logo_url": sp["sponsor_logo"] if sp["show_logo"] else None,
                    "naming_format": sp["naming_format"],
                }

            return {
                "venue": dict(venue),
                "sponsorship": sponsor_block,
                "display_name": display_name,
            }

    # ---------- Ad events ----------
    async def record_ad_event(self, sponsorship_id: int, event_type: str, meta_json: Optional[str] = None) -> None:
        if event_type not in ("impression", "click"):
            raise ValueError("event_type must be 'impression' or 'click'")
        async with (await aiosqlite.connect(self.db_path)) as db:
            await db.execute(
                """
                INSERT INTO sponsorship_ad_events (sponsorship_id, event_type, meta_json)
                VALUES (?, ?, ?)
                """,
                (sponsorship_id, event_type, meta_json),
            )
            await db.commit()

    async def get_ad_rollup(self, sponsorship_id: int) -> Dict[str, int]:
        async with (await aiosqlite.connect(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT event_type, COUNT(*) as cnt
                FROM sponsorship_ad_events
                WHERE sponsorship_id = ?
                GROUP BY event_type
                """,
                (sponsorship_id,),
            )
            rows = await cur.fetchall()
        out = {"impressions": 0, "clicks": 0}
        for r in rows:
            if r["event_type"] == "impression":
                out["impressions"] = r["cnt"]
            elif r["event_type"] == "click":
                out["clicks"] = r["cnt"]
        return out

    async def calculate_payout(self, sponsorship_id: int) -> Dict[str, int]:
        """Return payout breakdown for a sponsorship.

        Uses configured rates and split rules to determine how much of the
        sponsorship revenue should be paid to the venue versus retained by the
        platform.
        """
        rollup = await self.get_ad_rollup(sponsorship_id)
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
