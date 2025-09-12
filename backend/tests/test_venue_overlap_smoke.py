# File: backend/tests/test_venue_overlap_smoke.py
import pytest
from utils.db import get_conn
from backend.services.tour_service import TourService, TourError

DDL = """
CREATE TABLE IF NOT EXISTS venues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL, city TEXT, country TEXT, capacity INTEGER,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tours (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  band_id INTEGER NOT NULL, name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tour_stops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tour_id INTEGER NOT NULL,
  venue_id INTEGER NOT NULL,
  date_start TEXT NOT NULL,
  date_end TEXT NOT NULL,
  order_index INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  notes TEXT,
  is_recorded INTEGER NOT NULL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
"""

def setup_db(path):
    with get_conn(path) as conn:
        conn.executescript(DDL)

def test_overlap_blocked(tmp_path):
    db = str(tmp_path / "test_tour.db")
    setup_db(db)
    svc = TourService(db_path=db)

    v = svc.create_venue("Test Hall", "Oxford", "UK", 500)
    tour = svc.create_tour(band_id=1, name="Mini Tour")

    # First stop OK
    s1 = svc.add_stop(tour_id=tour["id"], venue_id=v["id"], date_start="2025-09-10", date_end="2025-09-10", order_index=0)

    # Overlapping stop at same venue should fail
    with pytest.raises(TourError):
        svc.add_stop(tour_id=tour["id"], venue_id=v["id"], date_start="2025-09-10", date_end="2025-09-10", order_index=1)
