import os
import tempfile
from pathlib import Path

import pytest

sys_path = Path(__file__).resolve().parents[3]
import sys
if str(sys_path) not in sys.path:
    sys.path.append(str(sys_path))

from backend.services.legacy_service import LegacyService
from backend.services.economy_service import EconomyService
from backend.services.merch_service import MerchService
from backend.models.merch import ProductIn, SKUIn


def setup_merch_with_legacy():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    legacy = LegacyService(db_path=path)
    econ.ensure_schema()
    legacy.ensure_schema()
    merch = MerchService(db_path=path, economy=econ, legacy=legacy)
    merch.ensure_schema()
    return merch, econ, legacy


def test_merch_purchase_logs_milestone():
    merch, econ, legacy = setup_merch_with_legacy()
    pid = merch.create_product(ProductIn(name="Shirt", category="clothing", band_id=1))
    sid = merch.create_sku(SKUIn(product_id=pid, price_cents=1000, stock_qty=10))
    econ.deposit(99, 10000)
    merch.purchase(99, items=[{"sku_id": sid, "qty": 1}])
    history = legacy.get_history(1)
    assert history and history[0]["category"] == "merch_revenue"
    assert legacy.compute_score(1) == 10


def test_leaderboard_ordering():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    legacy = LegacyService(db_path=path)
    legacy.ensure_schema()
    legacy.log_milestone(1, "chart_peak", "Hit #1", 100)
    legacy.log_milestone(2, "merch_revenue", "Sold merch", 20)
    legacy.log_milestone(1, "festival_revenue", "Festival", 30)
    lb = legacy.get_leaderboard()
    assert lb[0]["band_id"] == 1
    assert lb[0]["score"] == 130
