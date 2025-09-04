import pytest
from services.support_service import SupportService, SupportServiceError
from utils.db import get_conn


def _setup_db(path: str) -> None:
    """Create the minimal schema required for the support service."""
    with get_conn(path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT DEFAULT (datetime('now')),
                resolved_at TEXT
            )
            """
        )


def test_create_list_resolve(tmp_path):
    db = tmp_path / "db.sqlite"
    _setup_db(str(db))
    svc = SupportService(db_path=str(db))

    ticket_id = svc.create(user_id=1, subject="Cannot login", body="Please help")
    tickets = svc.list()
    assert len(tickets) == 1
    assert tickets[0]["id"] == ticket_id
    assert tickets[0]["status"] == "open"

    assert svc.resolve(ticket_id) is True
    tickets = svc.list()
    assert tickets[0]["status"] == "resolved"
    assert tickets[0]["resolved_at"] is not None


def test_create_validation(tmp_path):
    db = tmp_path / "db.sqlite"
    _setup_db(str(db))
    svc = SupportService(db_path=str(db))

    with pytest.raises(SupportServiceError):
        svc.create(user_id=1, subject="", body="No subject")

    with pytest.raises(SupportServiceError):
        svc.create(user_id=1, subject="Missing body", body="")

