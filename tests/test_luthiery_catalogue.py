import sqlite3

import pytest

from services.luthiery_catalogue_service import LuthieryCatalogueService


def _account(db_path, character_id=101, balance=100_000):
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                currency TEXT NOT NULL DEFAULT 'USD',
                balance_cents INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                amount_cents INTEGER NOT NULL,
                currency TEXT NOT NULL,
                src_account_id INTEGER,
                dest_account_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_id INTEGER NOT NULL,
                delta_cents INTEGER NOT NULL,
                balance_after INTEGER NOT NULL
            );
            """
        )
        conn.execute(
            "INSERT INTO accounts(user_id,currency,balance_cents) VALUES (?,?,?)",
            (character_id, "USD", balance),
        )


def test_catalogue_has_exact_five_parts_and_locked_progression(tmp_path):
    svc = LuthieryCatalogueService(str(tmp_path / "craft.db"))
    data = svc.catalogue(1)
    assert data["parts"] == ["body", "neck", "fretboard", "electronics", "hardware"]
    maple = next(row for row in data["materials"] if row["key"] == "luthier.material.maple")
    assert maple["locked"] is True


def test_purchase_is_character_owned_and_atomic(tmp_path):
    db = str(tmp_path / "craft.db")
    _account(db)
    svc = LuthieryCatalogueService(db)
    result = svc.purchase(101, "luthier.material.basswood", 2, 1)
    assert result["total_cents"] == 9000
    assert svc.inventory(101)[0]["quantity"] == 2
    assert svc.inventory(202) == []
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT balance_cents FROM accounts WHERE user_id=101").fetchone()[0] == 91_000
        assert conn.execute("SELECT COUNT(*) FROM material_purchase_history WHERE character_id=101").fetchone()[0] == 1


def test_locked_material_cannot_be_bought_and_money_is_unchanged(tmp_path):
    db = str(tmp_path / "craft.db")
    _account(db)
    svc = LuthieryCatalogueService(db)
    with pytest.raises(ValueError, match="locked"):
        svc.purchase(101, "luthier.material.ebony", 1, 1)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT balance_cents FROM accounts WHERE user_id=101").fetchone()[0] == 100_000
        assert conn.execute("SELECT COUNT(*) FROM material_purchase_history").fetchone()[0] == 0


def test_insufficient_funds_does_not_change_stock(tmp_path):
    db = str(tmp_path / "craft.db")
    _account(db, balance=100)
    svc = LuthieryCatalogueService(db)
    svc.ensure_schema()
    with sqlite3.connect(db) as conn:
        material_id = conn.execute("SELECT id FROM crafting_materials WHERE key='luthier.material.basswood'").fetchone()[0]
        before = conn.execute("SELECT quantity FROM luthier_supplier_stock WHERE material_id=?", (material_id,)).fetchone()[0]
    with pytest.raises(ValueError, match="funds"):
        svc.purchase(101, "luthier.material.basswood", 1, 1)
    with sqlite3.connect(db) as conn:
        after = conn.execute("SELECT quantity FROM luthier_supplier_stock WHERE material_id=?", (material_id,)).fetchone()[0]
    assert after == before
