from __future__ import annotations

from datetime import datetime, timedelta

from services.schedule_service import schedule_service


def daily_schedule_to_ics(user_id: int, date: str) -> str:
    """Return an ICS string for a user's schedule on a given date."""

    events = schedule_service.get_daily_schedule(user_id, date)
    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Rockmundo//Schedule//EN",
    ]
    base = datetime.fromisoformat(date)
    for entry in events:
        start_dt = base + timedelta(minutes=entry["slot"] * 15)
        duration = entry["activity"].get("duration_hours", 0) or 0
        end_dt = start_dt + timedelta(hours=duration)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{user_id}-{date}-{entry['slot']}",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{entry['activity']['name']}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


__all__ = ["daily_schedule_to_ics"]
