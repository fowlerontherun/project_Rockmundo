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

        conn.commit()
