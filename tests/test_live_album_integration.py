import sqlite3
from pathlib import Path
import sys
import asyncio

BASE_DIR = Path(__file__).resolve().parents[1]
sv = sys.path
sv.append(str(BASE_DIR))
sv.append(str(BASE_DIR / "backend"))

from backend.services.sales_service import SalesService
from backend.services.economy_service import EconomyService
from backend.services import chart_service


class DummyFameService:
    def __init__(self):
        self.calls = []

    def award_fame(self, band_id, source, amount, reason):
        self.calls.append((band_id, source, amount, reason))


def _setup_db(tmp_path: Path) -> Path:
    db = tmp_path / "live.db"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("CREATE TABLE bands (id INTEGER PRIMARY KEY, name TEXT)")
    cur.execute(
        "CREATE TABLE releases (id INTEGER PRIMARY KEY, title TEXT, band_id INTEGER, album_type TEXT)"
    )
    cur.execute(
        """
        CREATE TABLE chart_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chart_type TEXT,
            region TEXT,
            week_start TEXT,
            position INTEGER,
            song_id INTEGER,
            band_name TEXT,
            score REAL,
            generated_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    return db


def test_live_album_sale_updates_bank(tmp_path):
    db = _setup_db(tmp_path)
    economy = EconomyService(db_path=db)
    economy.ensure_schema()

    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO bands (id, name) VALUES (1, 'The Band')")
        cur.execute(
            "INSERT INTO releases (id, title, band_id, album_type) VALUES (1, 'Live', 1, 'live')"
        )
        conn.commit()

    sales = SalesService(db_path=db, economy=economy)
    asyncio.run(sales.ensure_schema())
    asyncio.run(sales.record_digital_sale(2, "album", 1, 1500, album_type="live"))

    assert economy.get_balance(1) == 1500


def test_live_album_chart_entry(tmp_path):
    db = _setup_db(tmp_path)
    economy = EconomyService(db_path=db)
    economy.ensure_schema()

    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO bands (id, name) VALUES (1, 'The Band')")
        cur.execute(
            "INSERT INTO releases (id, title, band_id, album_type) VALUES (1, 'Live', 1, 'live')"
        )
        conn.commit()

    sales = SalesService(db_path=db, economy=economy)
    asyncio.run(sales.ensure_schema())
    asyncio.run(sales.record_digital_sale(2, "album", 1, 1500, album_type="live"))

    chart_service.DB_PATH = db
    fame = DummyFameService()
    result = chart_service.calculate_album_chart(
        album_type="live", start_date="2024-01-01", fame_service=fame
    )

    assert result["entries"] and result["entries"][0][0] == 1
    assert fame.calls
