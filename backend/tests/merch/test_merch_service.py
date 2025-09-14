import os
import tempfile
from pathlib import Path

import pytest

sys_path = Path(__file__).resolve().parents[3]
import sys
if str(sys_path) not in sys.path:
    sys.path.append(str(sys_path))

from models.merch import ProductIn, SKUIn
from backend.services.economy_service import EconomyService
from backend.services.merch_service import MerchError, MerchService


def setup_service():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    svc = MerchService(db_path=path, economy=econ)
    svc.ensure_schema()
    return svc, econ


def test_inventory_depletion_and_revenue_distribution():
    svc, econ = setup_service()
    # Create a product for band 42
    pid = svc.create_product(ProductIn(name="Tour Hat", category="hat", band_id=42))
    sid = svc.create_sku(SKUIn(product_id=pid, price_cents=500, stock_qty=3))

    # Buyer funds and purchase two units
    econ.deposit(1, 5000)
    order_id = svc.purchase(1, items=[{"sku_id": sid, "qty": 2}])
    assert order_id > 0

    # Stock reduced and revenue paid to the band
    skus = svc.list_skus(pid)
    assert skus[0]["stock_qty"] == 1
    assert econ.get_balance(42) == 1000

    # Attempting to buy more than remaining inventory raises an error
    with pytest.raises(MerchError):
        svc.purchase(1, items=[{"sku_id": sid, "qty": 2}])

