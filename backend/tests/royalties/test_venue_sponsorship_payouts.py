import sqlite3

from backend.services.jobs_royalties import RoyaltyJobsService
from backend.services.venue_sponsorships_service import SponsorshipIn, VenueSponsorshipsService
from config import revenue


def test_venue_sponsorship_payout(tmp_path):
    db_path = tmp_path / "sponsor.db"
    svc = VenueSponsorshipsService(str(db_path))
    svc.ensure_schema()

    sid = svc.upsert_sponsorship(
        SponsorshipIn(
            venue_id=1,
            sponsor_name="MegaCorp",
            start_date="2024-01-01",
            end_date=None,
            is_active=True,
        )
    )

    svc.record_impression(sid)

    payout = svc.calculate_payout(sid)
    expected = revenue.SPONSOR_IMPRESSION_RATE_CENTS * revenue.SPONSOR_PAYOUT_SPLIT["venue"] // 100
    assert payout["impressions"] == 1
    assert payout["venue_cents"] == expected

    rsvc = RoyaltyJobsService(str(db_path))
    stats = rsvc.run_royalties("2000-01-01", "2030-01-01")
    stats = stats["global"]
    assert stats["sponsorship"] == 1

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT amount_cents FROM royalty_run_lines WHERE source='sponsorship'")
        amount = cur.fetchone()[0]
    assert amount == expected
