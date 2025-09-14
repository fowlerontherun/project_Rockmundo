"""Shop restocking helpers using :mod:`scheduler_service`."""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict

from backend.database import DB_PATH


def _update_quantity(table: str, shop_id: int, item_id: int, quantity: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        if table == "items":
            cur.execute(
                "UPDATE shop_items SET quantity = quantity + ? WHERE shop_id = ? AND item_id = ?",
                (quantity, shop_id, item_id),
            )
        else:
            cur.execute(
                "UPDATE shop_books SET quantity = quantity + ? WHERE shop_id = ? AND book_id = ?",
                (quantity, shop_id, item_id),
            )
        conn.commit()


def restock_handler(shop_id: int, kind: str, item_id: int, quantity: int) -> Dict[str, str]:
    """Scheduled task handler to restock an item or book."""
    table = "items" if kind == "item" else "books"
    _update_quantity(table, shop_id, item_id, quantity)
    return {"status": "restocked"}


def schedule_restock(
    shop_id: int, kind: str, item_id: int, interval: int, quantity: int
) -> Dict[str, int]:
    """Schedule recurring restocking for a shop item or book."""
    from services.scheduler_service import schedule_task

    run_at = (datetime.utcnow() + timedelta(days=interval)).isoformat()
    return schedule_task(
        "shop_restock",
        {
            "shop_id": shop_id,
            "kind": kind,
            "item_id": item_id,
            "quantity": quantity,
        },
        run_at,
        recurring=True,
        interval_days=interval,
    )


__all__ = ["restock_handler", "schedule_restock"]
