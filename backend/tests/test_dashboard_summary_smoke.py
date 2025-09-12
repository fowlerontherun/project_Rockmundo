# File: backend/tests/test_dashboard_summary_smoke.py
from backend.services.dashboard_service import DashboardService

from utils.db import get_conn

DDL = """
CREATE TABLE IF NOT EXISTS venues (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, city TEXT, country TEXT, capacity INTEGER, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS tours (id INTEGER PRIMARY KEY AUTOINCREMENT, band_id INTEGER, name TEXT, status TEXT DEFAULT 'draft', created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS tour_stops (id INTEGER PRIMARY KEY AUTOINCREMENT, tour_id INTEGER, venue_id INTEGER, date_start TEXT, date_end TEXT, order_index INTEGER, status TEXT DEFAULT 'pending', notes TEXT, is_recorded INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, title TEXT, body TEXT, created_at TEXT DEFAULT (datetime('now')), read_at TEXT);
CREATE TABLE IF NOT EXISTS sales_digital (id INTEGER PRIMARY KEY AUTOINCREMENT, quantity INTEGER, revenue REAL, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS sales_vinyl (id INTEGER PRIMARY KEY AUTOINCREMENT, quantity INTEGER, revenue REAL, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS streams (id INTEGER PRIMARY KEY AUTOINCREMENT, count INTEGER, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS world_pulse_rankings (name TEXT, rank INTEGER, pct_change REAL);
"""

def setup_db(path):
    with get_conn(path) as conn:
        conn.executescript(DDL)
        # seed minimal data
        conn.execute("INSERT INTO venues (name, city, country, capacity) VALUES ('Brixton', 'London', 'UK', 4900)")
        conn.execute("INSERT INTO tours (band_id, name, status) VALUES (1, 'UK Run', 'draft')")
        conn.execute("INSERT INTO tour_stops (tour_id, venue_id, date_start, date_end, order_index, status) VALUES (1, 1, date('now','+2 day'), date('now','+2 day'), 0, 'pending')")
        conn.execute("INSERT INTO notifications (user_id, type, title) VALUES (1, 'system', 'Welcome')")
        conn.execute("INSERT INTO sales_digital (quantity, revenue, created_at) VALUES (5, 3.99, date('now'))")
        conn.execute("INSERT INTO sales_vinyl (quantity, revenue, created_at) VALUES (2, 19.99, date('now'))")
        conn.execute("INSERT INTO streams (count, created_at) VALUES (100, date('now'))")
        conn.execute("INSERT INTO world_pulse_rankings (name, rank, pct_change) VALUES ('Demo Band', 1, 12.5)")

def test_dashboard_summary(tmp_path):
    db = str(tmp_path / "dash.db")
    setup_db(db)
    svc = DashboardService(db_path=db)
    summary = svc.summary(user_id=1, band_id=1, top_n=5)
    assert "next_show" in summary and summary["next_show"]
    assert "badge" in summary and isinstance(summary["badge"], dict)
    assert "pulse" in summary and len(summary["pulse"]) >= 1
    assert "music" in summary and "last_7d" in summary["music"]
    assert "chart_regions" in summary and isinstance(summary["chart_regions"], dict)
