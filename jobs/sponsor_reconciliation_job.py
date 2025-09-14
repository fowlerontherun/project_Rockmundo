"""Reconciliation job for sponsorship payouts vs royalty runs."""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Any, Dict

from services.jobs_royalties import RoyaltyJobsService
from services.sponsorship_service import SponsorshipService
from backend.utils.metrics import Counter

RECONCILIATION_JOB_FAILURES = Counter(
    "sponsor_reconciliation_failures_total",
    "Total sponsor reconciliation job failures",
)


def _sum_sponsorship_payouts(db_path: str) -> int:
    """Compute total venue payouts owed across all active sponsorships."""

    async def _inner() -> int:
        svc = SponsorshipService(db_path)
        sponsorships = await svc.list_venue_sponsorships(active_only=True)
        total = 0
        for s in sponsorships:
            payout = await svc.calculate_payout(s["id"])
            total += payout["venue_cents"]
        return total

    return asyncio.run(_inner())


def run(period_start: str, period_end: str, db: str) -> Dict[str, Any]:
    """Run royalties and verify sponsorship payouts are represented.

    Raises ``RuntimeError`` if the totals do not match.
    """

    rsvc = RoyaltyJobsService(db)
    stats_map = rsvc.run_royalties(period_start, period_end)
    stats = stats_map.get("global", next(iter(stats_map.values())))
    run_id = stats["run_id"]

    expected = _sum_sponsorship_payouts(db)

    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount_cents),0) FROM royalty_run_lines WHERE run_id=? AND source='sponsorship'",
            (run_id,),
        )
        actual = int(cur.fetchone()[0] or 0)

    try:
        if actual != expected:
            RECONCILIATION_JOB_FAILURES.labels().inc()
            raise RuntimeError(
                f"Sponsorship payouts mismatch: royalty lines={actual} expected={expected}"
            )
        return {"run_id": run_id, "sponsorship_payout_cents": actual}
    except Exception:
        RECONCILIATION_JOB_FAILURES.labels().inc()
        raise
