from datetime import datetime
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


def fetch_user_metrics(filters):
    return {
        "DAU": 1247,
        "MAU": 8123,
        "retention_rate": "48%",
        "avg_session_time": "61 minutes",
        "login_streaks": {"1_day": 350, "7_day": 120, "30_day": 25},
        "filters": filters.dict(),
    }


def fetch_economy_metrics(filters):
    return {
        "total_merch_sales": "$18,420",
        "skin_transactions": 614,
        "top_earner": "Band #4823 - $2,140",
        "royalties_paid": "$3,872",
        "active_marketplace_users": 388,
        "filters": filters.dict(),
    }


def fetch_event_metrics(filters):
    return {
        "gigs_played_today": 672,
        "albums_released_week": 134,
        "top_genres": ["Pop", "Jazz", "Electro"],
        "most_used_skills": ["Electric Guitar", "Songwriting"],
        "filters": filters.dict(),
    }


def fetch_community_metrics(filters):
    return {
        "avg_karma": 2.1,
        "reports_submitted": 4,
        "events_joined": 218,
        "alliances_formed": 39,
        "filters": filters.dict(),
    }


def fetch_error_logs():
    return [
        {
            "timestamp": str(datetime.utcnow()),
            "endpoint": "/bands/create",
            "error_type": "ValidationError",
            "message": "Band name required",
        },
        {
            "timestamp": str(datetime.utcnow()),
            "endpoint": "/skins/purchase",
            "error_type": "TransactionError",
            "message": "Insufficient balance",
        },
    ]


def _table_exists(cur, name: str) -> bool:
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    )
    return cur.fetchone() is not None


def fetch_shop_metrics(
    period_start: str | None = None,
    period_end: str | None = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """Summarize merch shop performance."""

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if not _table_exists(cur, "merch_orders"):
            return {"orders": 0, "revenue_cents": 0, "top_items": []}

        where = "WHERE o.status = 'confirmed'"
        params: List[Any] = []
        if period_start:
            where += " AND datetime(o.created_at) >= datetime(?)"
            params.append(f"{period_start} 00:00:00")
        if period_end:
            where += " AND datetime(o.created_at) <= datetime(?)"
            params.append(f"{period_end} 23:59:59")

        cur.execute(
            f"SELECT IFNULL(SUM(o.total_cents),0) AS revenue_cents, COUNT(*) AS orders "
            f"FROM merch_orders o {where}",
            params,
        )
        row = cur.fetchone() or {"revenue_cents": 0, "orders": 0}
        revenue = int(row["revenue_cents"] or 0)
        orders = int(row["orders"] or 0)

        top_items: List[Dict[str, Any]] = []
        if _table_exists(cur, "merch_order_items"):
            cur.execute(
                f"""
                SELECT oi.sku_id,
                       SUM(oi.qty) AS units,
                       SUM(oi.qty * oi.unit_price_cents) AS revenue_cents
                FROM merch_order_items oi
                JOIN merch_orders o ON o.id = oi.order_id
                {where}
                GROUP BY oi.sku_id
                ORDER BY units DESC
                LIMIT ?
                """,
                params + [limit],
            )
            top_items = [dict(r) for r in cur.fetchall()]

        return {"orders": orders, "revenue_cents": revenue, "top_items": top_items}
