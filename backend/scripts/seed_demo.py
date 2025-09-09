"""Seed the development database with demo data."""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from importlib import import_module
from pathlib import Path

# Ensure project root and backend package are on path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend.core.config import settings  # noqa: E402
from backend.core.security import hash_password  # noqa: E402

DEMO_EMAIL = "demo@rockmundo.test"
DEMO_PASSWORD = "demo123"
DEMO_DISPLAY_NAME = "Demo User"

SEEDS_DIR = ROOT / "backend" / "seeds"


def run_sql_seed(conn: sqlite3.Connection) -> None:
    sql_file = SEEDS_DIR / "demo_data.sql"
    if sql_file.exists():
        conn.executescript(sql_file.read_text(encoding="utf-8"))
        print(f"Loaded SQL seed data from {sql_file}")


def run_python_seeds(conn: sqlite3.Connection) -> None:
    for path in SEEDS_DIR.glob("*.py"):
        if path.name.startswith("__"):
            continue
        module = import_module(f"backend.seeds.{path.stem}")
        seed_fn = getattr(module, "seed", None)
        if callable(seed_fn):
            print(f"Running seed from {path.name}")
            seed_fn(conn)


def run_migrations(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            genre TEXT,
            trait TEXT,
            birthplace TEXT
        );

        CREATE TABLE IF NOT EXISTS avatars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            character_id INTEGER NOT NULL UNIQUE,
            nickname TEXT NOT NULL,
            body_type TEXT NOT NULL,
            skin_tone TEXT NOT NULL,
            face_shape TEXT NOT NULL,
            hair_style TEXT NOT NULL,
            hair_color TEXT NOT NULL,
            top_clothing TEXT NOT NULL,
            bottom_clothing TEXT NOT NULL,
            shoes TEXT NOT NULL,
            stamina INTEGER,
            charisma INTEGER,
            FOREIGN KEY(character_id) REFERENCES characters(id)
        );

        CREATE TABLE IF NOT EXISTS bands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            founder_id INTEGER,
            genre_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT,
            country TEXT,
            capacity INTEGER
        );

        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            duration_hours REAL NOT NULL,
            duration_days INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS daily_schedule (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            slot INTEGER NOT NULL,
            hour INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, date, slot)
        );
        """
    )


def create_demo_records(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # Demo user
    cur.execute("SELECT id FROM users WHERE email=?", (DEMO_EMAIL,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
    else:
        pw = hash_password(DEMO_PASSWORD)
        cur.execute(
            "INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)",
            (DEMO_EMAIL, pw, DEMO_DISPLAY_NAME),
        )
        user_id = cur.lastrowid

    # Character for avatar/band
    cur.execute(
        "INSERT INTO characters (name, genre, trait, birthplace) VALUES (?, ?, ?, ?)",
        ("Demo Character", "Rock", "neutral", "LA"),
    )
    character_id = cur.lastrowid

    # Avatar
    cur.execute(
        """
        INSERT INTO avatars (
            character_id, nickname, body_type, skin_tone, face_shape, hair_style,
            hair_color, top_clothing, bottom_clothing, shoes, stamina, charisma
        ) VALUES (?, ?, 'slim', 'pale', 'oval', 'short', 'black', 'tshirt', 'jeans', 'boots', 50, 50)
        """,
        (character_id, "DemoHero"),
    )

    # Band
    cur.execute(
        "INSERT INTO bands (name, founder_id, genre_id) VALUES (?, ?, ?)",
        ("Demo Band", character_id, 1),
    )

    # Sample venues
    venues = [
        ("Brixton Academy", "London", "UK", 4900),
        ("Barrowland Ballroom", "Glasgow", "UK", 1900),
        ("Paradiso", "Amsterdam", "NL", 1500),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO venues (name, city, country, capacity) VALUES (?, ?, ?, ?)",
        venues,
    )

    # Simple activity and daily schedule
    cur.execute(
        "INSERT OR IGNORE INTO activities (id, name, duration_hours, duration_days) VALUES (1, 'Practice', 2, 1)"
    )
    today = datetime.utcnow().date().isoformat()
    cur.execute(
        "INSERT OR IGNORE INTO daily_schedule (user_id, date, slot, hour, activity_id) VALUES (?, ?, 0, 9, 1)",
        (user_id, today),
    )

    conn.commit()

    # Print and write credentials
    print(f"Demo user credentials:\n  email: {DEMO_EMAIL}\n  password: {DEMO_PASSWORD}")
    readme_path = ROOT / "README.MD"
    creds_section = (
        f"## Demo Credentials\n\n- Email: {DEMO_EMAIL}\n- Password: {DEMO_PASSWORD}\n"
    )
    text = readme_path.read_text(encoding="utf-8")
    if DEMO_EMAIL not in text:
        readme_path.write_text(text.rstrip() + "\n\n" + creds_section, encoding="utf-8")


def main() -> None:
    db_path = Path(settings.database.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        run_migrations(conn)
        create_demo_records(conn)
    print("Database seeded with demo data.")


if __name__ == "__main__":  # pragma: no cover - utility script
    main()
