# backend/database.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "rockmundo.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # Users table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'player'
        )
        """)

        # Events table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            effect_type TEXT NOT NULL,
            skill_affected TEXT,
            duration_days INTEGER NOT NULL,
            trigger_chance REAL NOT NULL
        )
        """)

        # Active Events table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS active_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            skill_affected TEXT,
            start_date TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
        """)

        # Lifestyle table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS lifestyle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            sleep_hours REAL DEFAULT 7.0,
            drinking TEXT DEFAULT 'none',
            stress REAL DEFAULT 0.0,
            training_discipline REAL DEFAULT 50.0,
            mental_health REAL DEFAULT 100.0,
            last_updated TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # Admin audit log
        cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor INTEGER,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)

        # Social features
        cur.execute("""
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS friendships (
            user_a INTEGER NOT NULL,
            user_b INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_a, user_b)
        )
        """)

        # Jam sessions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS jam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS jam_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            stream_id TEXT NOT NULL,
            codec TEXT NOT NULL,
            premium INTEGER NOT NULL DEFAULT 0,
            started_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(session_id) REFERENCES jam_sessions(id)
        )
        """)

        # -------------------------------
        # Sponsorship schema (new)
        # -------------------------------

        # Minimal venues table (safe no-op if you already have one elsewhere)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
        """)

        # Sponsors table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sponsors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            website_url TEXT,
            logo_url TEXT,
            contact_email TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT
        )
        """)

        # Venue sponsorships
        cur.execute("""
        CREATE TABLE IF NOT EXISTS venue_sponsorships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venue_id INTEGER NOT NULL,
            sponsor_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            is_active INTEGER DEFAULT 1,
            naming_format TEXT DEFAULT '{sponsor} {venue}',
            show_logo INTEGER DEFAULT 1,
            show_website INTEGER DEFAULT 1,
            revenue_model TEXT DEFAULT 'CPM',    -- 'CPM','CPC','Fixed','Hybrid'
            revenue_cents_per_unit INTEGER,
            fixed_fee_cents INTEGER,
            currency TEXT DEFAULT 'USD',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT,
            FOREIGN KEY (venue_id) REFERENCES venues(id),
            FOREIGN KEY (sponsor_id) REFERENCES sponsors(id)
        )
        """)

        # Sponsorship ad events
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sponsorship_ad_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sponsorship_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,            -- 'impression' | 'click'
            occurred_at TEXT DEFAULT (datetime('now')),
            meta_json TEXT,
            FOREIGN KEY (sponsorship_id) REFERENCES venue_sponsorships(id)
        )
        """)

        # Helpful view for current effective sponsorship
        cur.execute("""
        CREATE VIEW IF NOT EXISTS v_current_venue_sponsorship AS
        SELECT
          vs.*
        FROM venue_sponsorships vs
        WHERE
          vs.is_active = 1
          AND date(vs.start_date) <= date('now')
          AND (vs.end_date IS NULL OR date(vs.end_date) >= date('now'));
        """)

        # Optional: Enforce single active sponsorship per venue
        cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_current_sponsor_per_venue
        ON venue_sponsorships(venue_id)
        WHERE is_active = 1 AND date(start_date) <= date('now') AND (end_date IS NULL OR date(end_date) >= date('now'));
        """)

        # Helpful indexes
        cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_venue_sponsorships_venue ON venue_sponsorships(venue_id);
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_venue_sponsorships_sponsor ON venue_sponsorships(sponsor_id);
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS ix_ad_events_sponsorship_time ON sponsorship_ad_events(sponsorship_id, occurred_at);
        """)

        # Song popularity tracking
        cur.execute("""
        CREATE TABLE IF NOT EXISTS song_popularity (
            song_id INTEGER PRIMARY KEY,
            score INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS song_popularity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            boost INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )
        """)

        # Quest definition tables
        cur.execute("""
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            initial_stage TEXT NOT NULL
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS quest_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quest_id INTEGER NOT NULL REFERENCES quests(id),
            stage_id TEXT NOT NULL,
            description TEXT NOT NULL,
            reward_type TEXT,
            reward_amount INTEGER
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS quest_branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage_id INTEGER NOT NULL REFERENCES quest_stages(id),
            choice TEXT NOT NULL,
            next_stage_id TEXT NOT NULL
        )
        """)

        conn.commit()
