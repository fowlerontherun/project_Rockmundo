import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))
from services.sales_service import SalesService


def _create_service(tmp_path):
    db = tmp_path / "sales.sqlite"
    svc = SalesService(db_path=str(db))
    svc.ensure_schema()
    return db, svc


def test_purchase_and_refund_vinyl_order(tmp_path):
    db, svc = _create_service(tmp_path)

    sku_id = svc.create_vinyl_sku(album_id=1, variant="standard", price_cents=1500, stock_qty=5)

    order_id = svc.purchase_vinyl(
        buyer_user_id=42,
        items=[{"sku_id": sku_id, "qty": 2}],
        shipping_address="123 Main St",
    )

    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("SELECT total_cents, status FROM vinyl_orders WHERE id = ?", (order_id,))
        assert cur.fetchone() == (3000, "confirmed")
        cur.execute(
            "SELECT sku_id, qty FROM vinyl_order_items WHERE order_id = ?",
            (order_id,),
        )
        assert cur.fetchone() == (sku_id, 2)

    result = svc.refund_vinyl_order(order_id, reason="defective")
    assert result == {"order_id": order_id, "refunded_cents": 3000}

    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("SELECT status FROM vinyl_orders WHERE id = ?", (order_id,))
        assert cur.fetchone()[0] == "refunded"
        cur.execute(
            "SELECT refunded_qty FROM vinyl_order_items WHERE order_id = ?",
            (order_id,),
        )
        assert cur.fetchone()[0] == 2
        cur.execute(
            "SELECT amount_cents, reason FROM vinyl_refunds WHERE order_id = ?",
            (order_id,),
        )
        assert cur.fetchone() == (3000, "defective")

