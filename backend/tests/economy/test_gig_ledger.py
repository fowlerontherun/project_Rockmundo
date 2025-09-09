import sqlite3
import types

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.economy.models import Account, LedgerEntry, Transaction as TransactionModel
from backend.services.economy_service import EconomyService
import backend.services.gig_service as gig_service


class DummyFanService:
    def get_band_fan_stats(self, band_id):
        return {"total_fans": 100, "average_loyalty": 50}

    def boost_fans_after_gig(self, band_id, city, attendance):
        pass


class DummySkillService:
    def train(self, uid, skill, amount):
        return types.SimpleNamespace(level=50)

    def get_category_multiplier(self, band_id, category):
        return 1.0

    def train_with_method(self, band_id, skill, method, difficulty):
        pass


def test_gig_completion_creates_ledger_entry(tmp_path):
    db_file = tmp_path / "gig.db"

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE gigs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            city TEXT,
            venue_size INTEGER,
            date TEXT,
            ticket_price INTEGER,
            status TEXT,
            attendance INTEGER,
            revenue INTEGER,
            fame_gain INTEGER
        )
        """
    )
    cur.execute(
        "INSERT INTO gigs (band_id, city, venue_size, date, ticket_price, status) VALUES (1, 'NY', 100, '2025-01-01', 10, 'scheduled')"
    )
    conn.commit()
    conn.close()

    gig_service.DB_PATH = db_file
    gig_service.economy_service = EconomyService(db_path=db_file)
    gig_service.economy_service.ensure_schema()
    gig_service.fan_service = DummyFanService()
    gig_service.skill_service = DummySkillService()

    result = gig_service.simulate_gig_result(1)

    engine = create_engine(f"sqlite:///{db_file}")
    with Session(engine) as session:
        acct_id = session.execute(
            select(Account.id).where(Account.user_id == 1)
        ).scalar_one()
        entry = session.execute(
            select(LedgerEntry)
            .where(LedgerEntry.account_id == acct_id)
            .order_by(LedgerEntry.id.desc())
        ).scalar_one()
        tx = session.execute(
            select(TransactionModel).where(TransactionModel.id == entry.transaction_id)
        ).scalar_one()
        assert entry.delta_cents == result["earnings"]
        assert tx.type == "gig"
