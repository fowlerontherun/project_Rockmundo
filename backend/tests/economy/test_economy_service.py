import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.economy_service import EconomyError, EconomyService


def setup_service():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    svc = EconomyService(db_path=path)
    svc.ensure_schema()
    return svc


def test_deposit_withdraw_transfer():
    svc = setup_service()
    svc.deposit(1, 1000)
    assert svc.get_balance(1) == 1000
    svc.withdraw(1, 200)
    assert svc.get_balance(1) == 800
    svc.deposit(2, 500)
    svc.transfer(1, 2, 300)
    assert svc.get_balance(1) == 500
    assert svc.get_balance(2) == 800


def test_withdraw_insufficient_funds():
    svc = setup_service()
    svc.deposit(1, 100)
    with pytest.raises(EconomyError):
        svc.withdraw(1, 200)


def test_transaction_history():
    svc = setup_service()
    svc.deposit(1, 100)
    svc.withdraw(1, 50)
    txns = svc.list_transactions(1)
    assert len(txns) == 2
    assert txns[0].type in {"deposit", "withdrawal", "transfer"}
