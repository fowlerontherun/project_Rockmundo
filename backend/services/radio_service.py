from __future__ import annotations

"""Service layer for handling radio streaming, scheduling and stats."""

import sqlite3
from pathlib import Path
from typing import Optional

from backend.services.economy_service import EconomyService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"
AD_REVENUE_CENTS = 1  # revenue per listener


class RadioService:
    def __init__(self, db_path: Optional[str] = None, economy: Optional[EconomyService] = None):
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(self.db_path)
        self.economy.ensure_schema()

    # ---------------- schema ----------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS radio_stations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    owner_id INTEGER NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS radio_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    recorded_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS radio_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id INTEGER NOT NULL,
                    episode_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL DEFAULT 'scheduled'
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS radio_subscriptions (
                    station_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    PRIMARY KEY (station_id, user_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS radio_listeners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    listened_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            conn.commit()

    # ---------------- stations & scheduling ----------------
    def create_station(self, owner_id: int, name: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO radio_stations(name, owner_id) VALUES (?, ?)", (name, owner_id))
            station_id = cur.lastrowid
            conn.commit()
        return {"id": station_id, "name": name, "owner_id": owner_id}

    def schedule_show(self, station_id: int, title: str, start_time: str) -> dict:
        """Create an episode and schedule it for broadcast."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO radio_episodes(station_id, title) VALUES (?, ?)", (station_id, title))
            episode_id = cur.lastrowid
            cur.execute(
                "INSERT INTO radio_schedule(station_id, episode_id, start_time) VALUES (?, ?, ?)",
                (station_id, episode_id, start_time),
            )
            schedule_id = cur.lastrowid
            conn.commit()
        return {
            "id": schedule_id,
            "station_id": station_id,
            "episode_id": episode_id,
            "start_time": start_time,
        }

    def subscribe(self, station_id: int, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO radio_subscriptions(station_id, user_id) VALUES (?, ?)",
                (station_id, user_id),
            )
            conn.commit()

    # ---------------- streaming ----------------
    def listen(self, station_id: int, user_id: int) -> int:
        """Record a listener if subscribed and pay out ad revenue."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM radio_subscriptions WHERE station_id=? AND user_id=?",
                (station_id, user_id),
            )
            if cur.fetchone() is None:
                raise PermissionError("User not subscribed to station")
            cur.execute(
                "INSERT INTO radio_listeners(station_id, user_id) VALUES (?, ?)",
                (station_id, user_id),
            )
            conn.commit()

        # deposit ad revenue to station owner
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT owner_id FROM radio_stations WHERE id=?", (station_id,))
            row = cur.fetchone()
        if row:
            self.economy.deposit(int(row[0]), AD_REVENUE_CENTS)
        return self.get_listener_count(station_id)

    def get_listener_count(self, station_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM radio_listeners WHERE station_id=?",
                (station_id,),
            )
            return int(cur.fetchone()[0])

    # For completeness: archive completed schedules
    def publish(self, schedule_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE radio_schedule SET status='completed' WHERE id=?",
                (schedule_id,),
            )
            conn.commit()
