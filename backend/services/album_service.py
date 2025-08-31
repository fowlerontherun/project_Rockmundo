import sqlite3
from datetime import datetime
from backend.database import DB_PATH
from backend.services import band_service


class AlbumService:
    def __init__(self, db: str | None = DB_PATH):
        self.db = db or DB_PATH

    def create_release(self, data: dict) -> dict:
        band_id = data.get("band_id")
        title = data.get("title")
        release_format = data.get("format")
        tracks = data.get("tracks", [])
        distribution_channels = ",".join(data.get("distribution_channels", []))

        if release_format == "ep" and len(tracks) > 4:
            raise ValueError("EPs cannot contain more than 4 tracks")

        total_runtime = sum(t.get("duration", 0) for t in tracks)

        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO releases (band_id, title, format, release_date, total_runtime, distribution_channels)
            VALUES (?, ?, ?, NULL, ?, ?)
            """,
            (band_id, title, release_format, total_runtime, distribution_channels),
        )
        release_id = cur.lastrowid

        for i, track in enumerate(tracks, start=1):
            cur.execute(
                """
                INSERT INTO tracks (release_id, title, duration, track_number)
                VALUES (?, ?, ?, ?)
                """,
                (release_id, track["title"], track["duration"], i),
            )

        conn.commit()
        conn.close()
        return {"status": "ok", "release_id": release_id}

    def list_releases_by_band(self, band_id: int) -> list:
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, title, format, release_date, total_runtime, distribution_channels
            FROM releases
            WHERE band_id = ?
            ORDER BY release_date DESC NULLS LAST
            """,
            (band_id,),
        )
        releases = cur.fetchall()
        conn.close()
        return [
            dict(
                zip(
                    [
                        "release_id",
                        "title",
                        "format",
                        "release_date",
                        "total_runtime",
                        "distribution_channels",
                    ],
                    row,
                )
            )
            for row in releases
        ]

    def update_release(self, release_id: int, updates: dict) -> dict:
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        for field, value in updates.items():
            cur.execute(f"UPDATE releases SET {field} = ? WHERE id = ?", (value, release_id))
        conn.commit()
        conn.close()
        return {"status": "ok", "message": "Release updated"}

    def publish_release(self, release_id: int) -> dict:
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()

        release_date = datetime.now().date()
        cur.execute("UPDATE releases SET release_date = ? WHERE id = ?", (release_date, release_id))

        cur.execute(
            "SELECT band_id FROM releases WHERE id = ?",
            (release_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"error": "Release not found"}

        band_id = row[0]
        fame_gain = 50
        revenue = 1000

        earnings = band_service.split_earnings(band_id, revenue, None)

        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "release_date": str(release_date),
            "fame_gain": fame_gain,
            "revenue": revenue,
            "earnings": earnings,
        }
