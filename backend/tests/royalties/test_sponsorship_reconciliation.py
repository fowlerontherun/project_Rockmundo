import asyncio
import sqlite3
from pathlib import Path

from backend.config import revenue
from backend.jobs import sponsor_reconciliation_job
from backend.services.sponsorship_service import SponsorshipService


def _setup_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE songs (id INTEGER PRIMARY KEY, band_id INTEGER)")
    cur.execute(
        "CREATE TABLE streams (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, song_id INTEGER, user_id INTEGER)"
    )
    cur.execute(
        """CREATE TABLE sponsors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        website_url TEXT,
        logo_url TEXT,
        contact_email TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT
    )"""
    )
    cur.execute(
        """CREATE TABLE venue_sponsorships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_id INTEGER NOT NULL,
        sponsor_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        is_active INTEGER NOT NULL,
        naming_format TEXT,
        show_logo INTEGER,
        show_website INTEGER,
        revenue_model TEXT,
        revenue_cents_per_unit INTEGER,
        fixed_fee_cents INTEGER,
        currency TEXT DEFAULT 'USD',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT
    )"""
    )
    cur.execute(
        """CREATE TABLE sponsorship_ad_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sponsorship_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        occurred_at TEXT DEFAULT (datetime('now')),
        meta_json TEXT
    )"""
    )
    conn.commit()
    conn.close()


def test_sponsorship_and_royalty_mix(tmp_path):
    db_path = tmp_path / "rev.db"
    _setup_db(str(db_path))

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO songs(id, band_id) VALUES (1, 1)")
    cur.execute(
        "INSERT INTO streams(created_at, song_id, user_id) VALUES ('2024-01-10 00:00:00', 1, 2)"
    )
    conn.commit()
    conn.close()

    svc = SponsorshipService(str(db_path))
    sponsor_id = asyncio.run(svc.create_sponsor({"name": "MegaCorp"}))
    sponsorship_id = asyncio.run(
        svc.create_venue_sponsorship(
            {
                "venue_id": 1,
                "sponsor_id": sponsor_id,
                "start_date": "2024-01-01",
                "end_date": None,
                "is_active": 1,
                "naming_format": "{sponsor} {venue}",
                "show_logo": 1,
                "show_website": 1,
                "revenue_model": "CPM",
                "revenue_cents_per_unit": None,
                "fixed_fee_cents": None,
                "currency": "USD",
            }
        )
    )
    asyncio.run(svc.record_ad_event(sponsorship_id, "impression"))

    result = sponsor_reconciliation_job.run(
        "2000-01-01", "2030-01-01", str(db_path)
    )

    expected = (
        revenue.SPONSOR_IMPRESSION_RATE_CENTS
        * revenue.SPONSOR_PAYOUT_SPLIT["venue"]
        // 100
    )
    assert result["sponsorship_payout_cents"] == expected

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT source FROM royalty_run_lines")
    sources = {row[0] for row in cur.fetchall()}
    conn.close()
    assert "streams" in sources and "sponsorship" in sources
