import importlib

from backend import database


def setup_service(tmp_path):
    db_file = tmp_path / "sched.db"
    database.DB_PATH = db_file
    database.init_db()

    from models import activity as activity_model
    from models import daily_schedule as schedule_model

    activity_model.DB_PATH = db_file
    schedule_model.DB_PATH = db_file

    analytics_module = importlib.reload(
        importlib.import_module("backend.services.analytics_service")
    )
    return analytics_module.schedule_analytics_service, activity_model, schedule_model

def test_weekly_totals_and_rest_compliance(tmp_path):
    svc, activity_model, schedule_model = setup_service(tmp_path)
    uid = 1
    week_start = "2024-01-01"

    work = activity_model.create_activity("Work", 2, "work")
    rest = activity_model.create_activity("Rest", 4, "rest")
    sleep = activity_model.create_activity("Sleep", 6, "sleep")

    schedule_model.add_entry(uid, week_start, 0, work)
    schedule_model.add_entry(uid, week_start, 4, rest)

    day2 = "2024-01-02"
    schedule_model.add_entry(uid, day2, 0, sleep)
    schedule_model.add_entry(uid, day2, 6, work)

    data = svc.weekly_totals(uid, week_start)
    assert data["totals"]["work"] == 4
    assert data["totals"]["rest"] == 4
    assert data["totals"]["sleep"] == 6

    rest_lookup = {r["date"]: r for r in data["rest"]}
    assert rest_lookup[week_start]["compliant"] is False
    assert rest_lookup[day2]["compliant"] is True

