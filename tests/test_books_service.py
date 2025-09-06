import sqlite3
from datetime import datetime
from pathlib import Path
import sys
import random

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))
sys.path.append(str(root_dir / "backend"))

from backend import database
from backend.models.book import Book
from backend.models.skill import Skill
from backend.services import scheduler_service
from backend.services.books_service import books_service
from backend.services.skill_service import skill_service
from backend.seeds.skill_seed import SKILL_NAME_TO_ID


def _setup_db(tmp_path):
    db = tmp_path / "sched.sqlite"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            params TEXT,
            run_at TEXT,
            recurring INTEGER,
            interval_days INTEGER,
            last_run TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    database.DB_PATH = db
    scheduler_service.DB_PATH = db
    skill_service.db_path = db
    return db


def _reset_services():
    books_service._books.clear()
    books_service._inventories.clear()
    books_service._id_seq = 1
    skill_service._skills.clear()
    skill_service._xp_today.clear()
    skill_service._method_history.clear()
    random.seed(0)


def test_queue_reading(tmp_path):
    _setup_db(tmp_path)
    _reset_services()

    book = books_service.create_book(
        Book(id=None, title="Guitar 101", genre="music", rarity="common", max_skill_level=5)
    )
    books_service.add_to_inventory(1, book.id)
    skill = Skill(id=1, name="guitar", category="instrument")

    books_service.queue_reading(1, book.id, skill, hours=1)

    conn = sqlite3.connect(scheduler_service.DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT event_type FROM scheduled_tasks")
    rows = cur.fetchall()
    conn.close()
    assert rows == [("complete_reading",)]


def test_reading_completion(tmp_path):
    _setup_db(tmp_path)
    _reset_services()

    book = books_service.create_book(
        Book(id=None, title="Drums", genre="music", rarity="rare", max_skill_level=10)
    )
    books_service.add_to_inventory(1, book.id)
    skill = Skill(id=2, name="drums", category="instrument")

    books_service.queue_reading(1, book.id, skill, hours=1)

    conn = sqlite3.connect(scheduler_service.DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE scheduled_tasks SET run_at = ?", (datetime.utcnow().isoformat(),))
    conn.commit()
    conn.close()

    scheduler_service.run_due_tasks()

    inst = skill_service._skills[(1, skill.id)]
    assert inst.xp == 10
    assert book.id not in books_service._inventories.get(1, [])


def test_book_level_cap(tmp_path):
    _setup_db(tmp_path)
    _reset_services()

    skill = Skill(id=3, name="bass", category="instrument", xp=150, level=2)
    skill_service._skills[(1, skill.id)] = skill

    book = books_service.create_book(
        Book(id=None, title="Advanced", genre="music", rarity="epic", max_skill_level=3)
    )
    books_service.add_to_inventory(1, book.id)

    books_service.queue_reading(1, book.id, skill, hours=20)

    conn = sqlite3.connect(scheduler_service.DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE scheduled_tasks SET run_at = ?", (datetime.utcnow().isoformat(),))
    conn.commit()
    conn.close()

    scheduler_service.run_due_tasks()

    inst = skill_service._skills[(1, skill.id)]
    assert inst.level == 3
    assert inst.xp == 299


def test_music_theory_reading(tmp_path):
    _setup_db(tmp_path)
    _reset_services()

    book = books_service.create_book(
        Book(id=None, title="Theory", genre="music", rarity="common", max_skill_level=5)
    )
    books_service.add_to_inventory(1, book.id)
    skill = Skill(
        id=SKILL_NAME_TO_ID["music_theory"], name="music_theory", category="creative"
    )

    books_service.queue_reading(1, book.id, skill, hours=1)

    conn = sqlite3.connect(scheduler_service.DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE scheduled_tasks SET run_at = ?", (datetime.utcnow().isoformat(),))
    conn.commit()
    conn.close()

    scheduler_service.run_due_tasks()

    inst = skill_service._skills[(1, skill.id)]
    assert inst.xp > 0

