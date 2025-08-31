import json
import sqlite3
from datetime import datetime, timedelta

from backend.database import DB_PATH
from backend.services import chart_service, fan_service, song_popularity_service
from backend.services.skill_service import skill_service

# Map event_type to handler functions
EVENT_HANDLERS = {
    "fan_decay": fan_service.decay_fan_loyalty,
    "weekly_charts": chart_service.calculate_weekly_chart,
    "skill_decay": skill_service.decay_all,
    "aggregate_global_popularity": song_popularity_service.aggregate_global_popularity,
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