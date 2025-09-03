#!/usr/bin/env python3
"""One-time migration script to convert daily_schedule.hour to slot.

Each existing entry's hour is multiplied by four to produce the new slot value
(0-95 representing 15-minute increments). Run this script once after deploying
the new schema.
"""

import sqlite3
from backend.database import DB_PATH


def migrate() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(daily_schedule)")
        columns = [row[1] for row in cur.fetchall()]
        if "hour" in columns:
            cur.execute("ALTER TABLE daily_schedule RENAME TO daily_schedule_old")
            cur.execute(
                """
                CREATE TABLE daily_schedule (
                    user_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    slot INTEGER NOT NULL,
                    activity_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, date, slot),
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(activity_id) REFERENCES activities(id)
                )
                """
            )
            cur.execute(
                """
                INSERT INTO daily_schedule (user_id, date, slot, activity_id)
                SELECT user_id, date, hour * 4 AS slot, activity_id
                FROM daily_schedule_old
                """
            )
            cur.execute("DROP TABLE daily_schedule_old")
            conn.commit()
            print("Migration completed: daily_schedule.hour -> slot")
        else:
            print("No migration needed; slot column already present")


if __name__ == "__main__":
    migrate()
