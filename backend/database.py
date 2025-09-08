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
            role TEXT DEFAULT 'player',
            learning_style TEXT DEFAULT 'balanced'
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
            nutrition REAL DEFAULT 70.0,
            fitness REAL DEFAULT 70.0,
            appearance_score REAL DEFAULT 50.0,
            exercise_minutes REAL DEFAULT 0.0,
            last_exercise TEXT,
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

        # Festival proposals
        cur.execute("""
        CREATE TABLE IF NOT EXISTS festival_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposer_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            genre TEXT,
            vote_count INTEGER NOT NULL DEFAULT 0,
            approved INTEGER NOT NULL DEFAULT 0
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            region_code TEXT NOT NULL DEFAULT 'global',
            platform TEXT NOT NULL DEFAULT 'any',
            popularity_score REAL NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS song_popularity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            region_code TEXT NOT NULL DEFAULT 'global',
            platform TEXT NOT NULL DEFAULT 'any',
            source TEXT NOT NULL,
            boost INTEGER NOT NULL,
            details TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS song_popularity_forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            forecast_date TEXT NOT NULL,
            predicted_score REAL NOT NULL,
            lower REAL,
            upper REAL,
            created_at TEXT NOT NULL,
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

        # Setlist revisions for collaborative editing
        cur.execute("""
        CREATE TABLE IF NOT EXISTS setlist_revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setlist_id INTEGER NOT NULL,
            setlist TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            approved INTEGER DEFAULT 0
        )
        """)

        # Tour collaborations linking multiple bands
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tour_collaborations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                band_ids TEXT NOT NULL,
                setlist TEXT NOT NULL,
                revenue_split TEXT NOT NULL,
                schedule TEXT,
                expenses TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )

        # Learning sessions for skill training
        cur.execute("""
        CREATE TABLE IF NOT EXISTS learning_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            method TEXT NOT NULL,
            duration INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            scheduled_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # Optional tutor metadata
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tutors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            hourly_rate INTEGER NOT NULL,
            level_requirement INTEGER NOT NULL DEFAULT 0
        )
        """)

        # University courses
        cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_target TEXT NOT NULL,
            duration INTEGER NOT NULL,
            prerequisites TEXT,
            prestige INTEGER NOT NULL DEFAULT 0
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            completed INTEGER NOT NULL DEFAULT 0,
            enrolled_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
        """)

        # Apprenticeships linking mentors and students
        cur.execute("""
        CREATE TABLE IF NOT EXISTS apprenticeships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            mentor_id INTEGER NOT NULL,
            mentor_type TEXT NOT NULL,
            skill_id INTEGER NOT NULL,
            duration_days INTEGER NOT NULL,
            level_requirement INTEGER NOT NULL DEFAULT 0,
            start_date TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
        )
        """)

        # Daily loop table for login streaks and challenges
        cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_loop (
            user_id INTEGER PRIMARY KEY,
            login_streak INTEGER DEFAULT 0,
            last_login TEXT,
            current_challenge TEXT,
            challenge_progress INTEGER DEFAULT 0,
            reward_claimed INTEGER DEFAULT 0,
            catch_up_tokens INTEGER DEFAULT 0,
            challenge_tier INTEGER DEFAULT 1,
            weekly_goal_count INTEGER DEFAULT 0,
            tier_progress INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # Weekly reward drops linked to the daily loop
        cur.execute("""
        CREATE TABLE IF NOT EXISTS weekly_drops (
            user_id INTEGER NOT NULL,
            drop_date TEXT NOT NULL,
            reward TEXT NOT NULL,
            claimed INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, drop_date),
            FOREIGN KEY(user_id) REFERENCES daily_loop(user_id)
        )
        """)

        # Tier reward track defining rewards for each tier
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tier_tracks (
            tier INTEGER PRIMARY KEY,
            reward TEXT NOT NULL
        )
        """)

        # User settings table for profile preferences
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'light',
            bio TEXT,
            links TEXT,
            timezone TEXT DEFAULT 'UTC',
            auto_reschedule INTEGER DEFAULT 1
        )
        """)

        # Activities table for user tasks
        cur.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            duration_hours REAL NOT NULL,
            duration_days INTEGER NOT NULL DEFAULT 1,
            category TEXT,
            required_skill TEXT,
            energy_cost INTEGER NOT NULL DEFAULT 0,
            rewards_json TEXT
        )
        """)

        # Default schedule template per user
        cur.execute("""
        CREATE TABLE IF NOT EXISTS default_schedule (
            user_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL,
            hour INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, day_of_week, hour),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """)

        # Named default schedule templates
        cur.execute("""
        CREATE TABLE IF NOT EXISTS default_schedule_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS default_schedule_entries (
            template_id INTEGER NOT NULL,
            hour INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            PRIMARY KEY (template_id, hour),
            FOREIGN KEY(template_id) REFERENCES default_schedule_templates(id),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """)

        # Recurring schedule templates
        cur.execute("""
        CREATE TABLE IF NOT EXISTS recurring_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pattern TEXT NOT NULL,
            hour INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """)

        # Weekly schedule entries linking users to activities
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS weekly_schedule (
                user_id INTEGER NOT NULL,
                week_start TEXT NOT NULL,
                day TEXT NOT NULL,
                slot INTEGER NOT NULL DEFAULT 0,
                activity_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, week_start, day, slot),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(activity_id) REFERENCES activities(id)
            )
            """
        )

        # Daily schedule entries linking users to activities
        cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_schedule (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            slot INTEGER NOT NULL,
            hour INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, date, slot),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """)

        # Next-day schedule holding rescheduled activities
        cur.execute("""
        CREATE TABLE IF NOT EXISTS next_day_schedule (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            slot INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, date, slot),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """)

        # Audit log for schedule changes capturing before/after states
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schedule_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                slot INTEGER NOT NULL,
                before_state TEXT,
                after_state TEXT,
                changed_at TEXT DEFAULT (datetime('now'))
            )
            """,
        )

        # Band schedule entries linking bands to activities
        cur.execute("""
        CREATE TABLE IF NOT EXISTS band_schedule (
            band_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            slot INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            PRIMARY KEY (band_id, date, slot),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """)

        # Logs and progression for scheduled activities
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                slot INTEGER NOT NULL DEFAULT 0,
                activity_id INTEGER NOT NULL,
                outcome_json TEXT NOT NULL,
                PRIMARY KEY (user_id, date, slot),
                FOREIGN KEY(user_id, date, slot) REFERENCES daily_schedule(user_id, date, slot),
                FOREIGN KEY(activity_id) REFERENCES activities(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_xp (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_energy (
                user_id INTEGER PRIMARY KEY,
                energy INTEGER NOT NULL DEFAULT 100,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        # Support tickets allow players to file issues and admins to resolve them
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT DEFAULT (datetime('now')),
                resolved_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.commit()
