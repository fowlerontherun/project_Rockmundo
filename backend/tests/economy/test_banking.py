import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.economy_service import EconomyError, EconomyService
from backend.services.property_service import PropertyService
from backend.services.business_service import BusinessService


def setup_env():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    prop = PropertyService(db_path=path, economy=econ)
    prop.ensure_schema()
    biz = BusinessService(db_path=path, economy=econ)
    biz.ensure_schema()
    return econ, prop, biz


def test_mortgage_property_creates_loan():
    econ, prop, _ = setup_env()
    pid = prop.buy_property(
        owner_id=1,
        name="House",
        property_type="home",
        location="LA",
        price_cents=1000,
        base_rent=100,
        mortgage_rate=0.05,
    )
    assert pid > 0
    loans = econ.list_loans(1)
    assert loans and loans[0].balance_cents == 1000
    assert econ.get_balance(1) == 0


def test_investment_interest_returns():
    econ, _, biz = setup_env()
    econ.deposit(1, 1000)
    acct = biz.invest(1, 500, 0.1)
    interest = biz.collect_investment_returns(acct)
    assert interest == 50
    assert econ.get_balance(1) == 550


def test_currency_conversion_and_missing_rate():
    econ, _, _ = setup_env()
    econ.set_exchange_rate("USD", "EUR", 0.5)
    assert econ.convert_currency(200, "USD", "EUR") == 100
    with pytest.raises(EconomyError):
        econ.convert_currency(100, "EUR", "JPY")


def test_create_loan_invalid_amount():
    econ, _, _ = setup_env()
    with pytest.raises(EconomyError):
        econ.create_loan(1, 0, 0.05, 10)
