import sqlite3
from datetime import datetime, timedelta

from backend.services.achievement_service import AchievementService
from backend.services.legacy_service import LegacyService

from database import DB_PATH

achievement_service = AchievementService(DB_PATH)
legacy_service = LegacyService(DB_PATH)
legacy_service.ensure_schema()


def calculate_weekly_chart(
    chart_type: str = "Global Top 100", region: str = "global", start_date: str = None
) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if not start_date:
        # Default to last Monday
        today = datetime.utcnow().date()
        start_date = (today - timedelta(days=today.weekday())).isoformat()

    # Retrieve stream counts and revenues per song in date range
    cur.execute(
        """
        SELECT s.id, s.title, b.id, b.name,
               SUM(CASE WHEN str.timestamp BETWEEN ? AND ?
                        AND (str.region = ? OR str.region IS NULL)
                   THEN 1 ELSE 0 END) AS streams,
               SUM(CASE WHEN e.source_type = 'stream' AND e.source_id = s.id
                   THEN e.amount ELSE 0 END) AS revenue
        FROM songs s
        JOIN bands b ON s.band_id = b.id
        LEFT JOIN streams str ON str.song_id = s.id
        LEFT JOIN earnings e ON e.source_type = 'stream' AND e.source_id = s.id
        WHERE (str.timestamp BETWEEN ? AND ? AND (str.region = ? OR str.region IS NULL))
              OR e.timestamp BETWEEN ? AND ?
        GROUP BY s.id
        """,
        (
            start_date,
            datetime.utcnow().isoformat(),
            region,
            start_date,
            datetime.utcnow().isoformat(),
            region,
            start_date,
            datetime.utcnow().isoformat(),
        ),
    )

    rows = cur.fetchall()
    scoring = []
    for song_id, title, band_id, band_name, streams, revenue in rows:
        score = streams * 0.4 + revenue * 10
        scoring.append((song_id, title, band_id, band_name, score))

    # Sort and take top 100
    scoring.sort(key=lambda x: x[3], reverse=True)
    top = scoring[:100]

    # Persist chart entries
    for position, (song_id, title, band_id, band_name, score) in enumerate(top, start=1):
        cur.execute(
            """
            INSERT INTO chart_entries
            (chart_type, region, week_start, position, song_id, band_name, score, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chart_type,
                region,
                start_date,
                position,
                song_id,
                band_name,
                score,
                datetime.utcnow().isoformat(),
            ),
        )

    conn.commit()
    conn.close()

    for position, (_, _, band_id, _, _) in enumerate(top, start=1):
        if position == 1:
            try:
                achievement_service.grant(band_id, "chart_topper")
            except Exception:
                pass
            try:
                legacy_service.log_milestone(
                    band_id,
                    "chart_peak",
                    f"{chart_type} #1",
                    100,
                )
            except Exception:
                pass

    top_entries = [(s, t, b_name, sc) for (s, t, _, b_name, sc) in top]
    return {
        "chart_type": chart_type,
        "region": region,
        "week_start": start_date,
        "entries": top_entries,
    }


def get_chart(chart_type: str, region: str, week_start: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT position, song_id, band_name, score
        FROM chart_entries
        WHERE chart_type = ? AND region = ? AND week_start = ?
        ORDER BY position ASC
        """,
        (chart_type, region, week_start),
    )
    rows = cur.fetchall()
    conn.close()

    return [dict(zip(["position", "song_id", "band_name", "score"], row)) for row in rows]


def get_historical_charts(chart_type: str, region: str, weeks: int = 4) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get distinct week_starts for the chart type
    cur.execute(
        """
        SELECT DISTINCT week_start
        FROM chart_entries
        WHERE chart_type = ? AND region = ?
        ORDER BY week_start DESC
        LIMIT ?
        """,
        (chart_type, region, weeks),
    )
    dates = [row[0] for row in cur.fetchall()]

    history = {}
    for wk in dates:
        history[wk] = get_chart(chart_type, region, wk)

    conn.close()
    return history


def calculate_album_chart(
    album_type: str = "studio",
    start_date: str | None = None,
    region: str = "global",
    fame_service=None,
) -> dict:
    """Generate a simple album chart based on digital sales revenue.

    Parameters
    ----------
    album_type:
        Filter releases by album type (``"studio"`` or ``"live"``).
    fame_service:
        Optional service providing ``award_fame`` used to grant fame to the
        chart topper.
    region:
        Geographic region or country code for which to generate the chart.
    """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if not start_date:
        today = datetime.utcnow().date()
        start_date = (today - timedelta(days=today.weekday())).isoformat()

    cur.execute(
        """
        SELECT r.id, r.title, b.id, b.name, SUM(d.price_cents) as revenue
        FROM digital_sales d
        JOIN releases r ON r.id = d.work_id
        JOIN bands b ON b.id = r.band_id
        WHERE d.work_type = 'album'
          AND r.album_type = ?
          AND d.created_at BETWEEN ? AND ?
        GROUP BY r.id, r.title, b.id, b.name
        """,
        (album_type, start_date, datetime.utcnow().isoformat()),
    )

    rows = cur.fetchall()
    rows.sort(key=lambda x: x[4], reverse=True)
    top = rows[:100]

    for position, (album_id, title, band_id, band_name, revenue) in enumerate(
        top, start=1
    ):
        cur.execute(
            """
            INSERT INTO chart_entries
            (chart_type, region, week_start, position, song_id, band_name, score, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{album_type.title()} Album Chart",
                region,
                start_date,
                position,
                album_id,
                band_name,
                revenue,
                datetime.utcnow().isoformat(),
            ),
        )

    conn.commit()
    conn.close()

    if fame_service and top:
        try:
            fame_service.award_fame(
                top[0][2], "album_chart", 100, f"{album_type} album #1"
            )
        except Exception:
            pass

    entries = [(a, t, b, r) for (a, t, _, b, r) in top]
    return {
        "chart_type": f"{album_type.title()} Album Chart",
        "region": region,
        "week_start": start_date,
        "entries": entries,
    }
