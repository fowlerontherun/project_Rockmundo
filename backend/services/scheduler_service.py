import json
import sqlite3
from datetime import date, datetime, timedelta

from backend.database import DB_PATH
from backend.models import daily_loop
from backend.services import chart_service, fan_service, song_popularity_service
from backend.services.activity_processor import process_previous_day
from backend.services.schedule_service import schedule_service
from backend.services.books_service import books_service
from backend.services.peer_learning_service import run_scheduled_session
from backend.services.skill_service import skill_service
from backend.services.social_sentiment_service import social_sentiment_service
from backend.services.song_popularity_forecast import forecast_service
from backend.models.notification_models import (
    alert_no_plan,
    alert_pending_outcomes,
)


def _plan_reminder(user_id: int, day: str) -> dict:
    """Send a reminder if the user lacks a schedule for ``day``."""

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM daily_schedule WHERE user_id = ? AND date = ? LIMIT 1",
        (user_id, day),
    )
    has_plan = cur.fetchone() is not None
    conn.close()
    if not has_plan:
        alert_no_plan(user_id, day)
        return {"status": "sent"}
    return {"status": "skipped"}


def _outcome_reminder(user_id: int, day: str) -> dict:
    """Notify if scheduled activities for ``day`` lack outcomes."""

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM daily_schedule WHERE user_id = ? AND date = ?",
        (user_id, day),
    )
    scheduled = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM activity_log WHERE user_id = ? AND date = ?",
        (user_id, day),
    )
    processed = cur.fetchone()[0]
    conn.close()
    if scheduled > processed:
        alert_pending_outcomes(user_id, day)
        return {"status": "sent"}
    return {"status": "skipped"}

# Map event_type to handler functions
def _daily_loop_reset_wrapper() -> None:
    """Rotate challenge and seed schedules for inactive users."""
    daily_loop.rotate_daily_challenge()
    today = date.today().isoformat()
    weekday = date.today().strftime("%A").lower()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id, last_login FROM daily_loop")
    users = cur.fetchall()
    conn.close()
    for user_id, last_login in users:
        if last_login != today:
            plan = schedule_service.get_default_plan(user_id, weekday)
            for entry in plan:
                schedule_service.schedule_activity(
                    user_id, today, entry["hour"], entry["activity"]["id"]
                )


EVENT_HANDLERS = {
    "fan_decay": fan_service.decay_fan_loyalty,
    "weekly_charts": chart_service.calculate_weekly_chart,
    "skill_decay": skill_service.decay_all,
    "aggregate_global_popularity": song_popularity_service.aggregate_global_popularity,
    "song_popularity_forecast": forecast_service.recompute_all,
    "social_sentiment": social_sentiment_service.process_song,
    "complete_reading": books_service.complete_reading,
    "peer_learning": run_scheduled_session,
    "daily_loop_reset": daily_loop.rotate_daily_challenge,
    "daily_activity_resolution": process_previous_day,
    "daily_loop_reset": _daily_loop_reset_wrapper,
    "plan_reminder": _plan_reminder,
    "outcome_reminder": _outcome_reminder,
    # Add more event handlers here as needed
}

def schedule_task(event_type: str, params: dict, run_at: str, recurring: bool=False, interval_days: int=None) -> dict:
    """
    Schedule a new task.
    event_type: key in EVENT_HANDLERS
    params: dict passed to handler
    run_at: ISO datetime string
    recurring: whether to repeat
    interval_days: days between repeats
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(""" 
        INSERT INTO scheduled_tasks 
        (event_type, params, run_at, recurring, interval_days, last_run) 
        VALUES (?, ?, ?, ?, ?, NULL)
    """, (event_type, json.dumps(params), run_at, int(recurring), interval_days))
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"status": "ok", "task_id": task_id}

def get_scheduled_tasks() -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(""" 
        SELECT id, event_type, params, run_at, recurring, interval_days 
        FROM scheduled_tasks
    """)
    rows = cur.fetchall()
    conn.close()
    tasks = []
    for row in rows:
        tasks.append({
            "task_id": row[0],
            "event_type": row[1],
            "params": json.loads(row[2]),
            "run_at": row[3],
            "recurring": bool(row[4]),
            "interval_days": row[5]
        })
    return tasks

def delete_task(task_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Task deleted"}

def run_due_tasks() -> dict:
    """
    Run all tasks where run_at <= now.
    If recurring, reschedule next run.
    """
    now_iso = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(""" 
        SELECT id, event_type, params, recurring, interval_days 
        FROM scheduled_tasks
        WHERE run_at <= ?
    """, (now_iso,))
    due = cur.fetchall()

    results = []
    for task in due:
        task_id, event_type, params_json, recurring, interval_days = task
        params = json.loads(params_json)
        handler = EVENT_HANDLERS.get(event_type)
        if handler:
            try:
                # Call handler with params
                result = handler(**params) if isinstance(params, dict) else handler(params)
                results.append({"task_id": task_id, "result": result})
            except Exception as e:
                results.append({"task_id": task_id, "error": str(e)})

        if recurring and interval_days:
            # Schedule next
            next_run = datetime.utcnow() + timedelta(days=interval_days)
            cur.execute(""" 
                UPDATE scheduled_tasks 
                SET run_at = ?, last_run = ? 
                WHERE id = ?
            """, (next_run.isoformat(), now_iso, task_id))
        else:
            # Delete non-recurring
            cur.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))

    conn.commit()
    conn.close()
    return {"status": "ok", "executed": len(due), "details": results}


def schedule_daily_loop_reset() -> dict:
    """Ensure a daily task exists to rotate challenges."""
    tasks = get_scheduled_tasks()
    for task in tasks:
        if task["event_type"] == "daily_loop_reset":
            return {"status": "exists"}
    next_run = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return schedule_task(
        "daily_loop_reset",
        {},
        next_run.isoformat(),
        recurring=True,
        interval_days=1,
    )


def schedule_daily_activity_resolution() -> dict:
    """Ensure a nightly job exists to resolve scheduled activities."""
    tasks = get_scheduled_tasks()
    for task in tasks:
        if task["event_type"] == "daily_activity_resolution":
            return {"status": "exists"}
    next_run = (
        datetime.utcnow().replace(hour=0, minute=5, second=0, microsecond=0)
        + timedelta(days=1)
    )
    return schedule_task(
        "daily_activity_resolution",
        {},
        next_run.isoformat(),
        recurring=True,
        interval_days=1,
    )


def schedule_plan_reminder(user_id: int, day: str, run_at: str) -> dict:
    """Schedule a one-off reminder to plan the day."""

    return schedule_task(
        "plan_reminder",
        {"user_id": user_id, "day": day},
        run_at,
    )


def schedule_outcome_reminder(user_id: int, day: str, run_at: str) -> dict:
    """Schedule a reminder to process pending outcomes."""

    return schedule_task(
        "outcome_reminder",
        {"user_id": user_id, "day": day},
        run_at,
    )
