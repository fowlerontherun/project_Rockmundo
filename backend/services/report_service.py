import sqlite3
from typing import Dict

from backend.database import DB_PATH


class ReportService:
    """Aggregate scheduled and completed activity hours."""

    def weekly_summary(self, user_id: int, week_start: str) -> Dict[str, float]:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            # Sum scheduled hours from weekly_schedule
            cur.execute(
                """
                SELECT COALESCE(SUM(a.duration_hours), 0)
                FROM weekly_schedule ws
                JOIN activities a ON ws.activity_id = a.id
                WHERE ws.user_id = ? AND ws.week_start = ?
                """,
                (user_id, week_start),
            )
            scheduled = cur.fetchone()[0] or 0.0
            # Sum completed hours from activity_log
            cur.execute(
                """
                SELECT COALESCE(SUM(a.duration_hours), 0)
                FROM activity_log al
                JOIN activities a ON al.activity_id = a.id
                WHERE al.user_id = ? AND al.date BETWEEN ? AND date(?, '+6 days')
                """,
                (user_id, week_start, week_start),
            )
            completed = cur.fetchone()[0] or 0.0
        return {
            "week_start": week_start,
            "scheduled_hours": scheduled,
            "completed_hours": completed,
        }


report_service = ReportService()

__all__ = ["ReportService", "report_service"]
