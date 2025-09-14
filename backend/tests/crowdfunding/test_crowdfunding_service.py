from services.crowdfunding_service import CrowdfundingService
from services.economy_service import EconomyService


def test_pledge_and_distribution(tmp_path):
    db = tmp_path / "db.sqlite"
    economy = EconomyService(db_path=str(db))
    economy.ensure_schema()
    svc = CrowdfundingService(db_path=str(db), economy=economy)
    svc.ensure_schema()

    # Seed backers with funds
    economy.deposit(user_id=1, amount_cents=1000)
    economy.deposit(user_id=2, amount_cents=1000)

    campaign_id = svc.create_campaign(creator_id=3, goal_cents=1000, creator_share=0.5, backer_share=0.5)

    svc.pledge(campaign_id=campaign_id, backer_id=1, amount_cents=600)
    svc.pledge(campaign_id=campaign_id, backer_id=2, amount_cents=400)

    svc.complete_campaign(campaign_id)

    assert economy.get_balance(1) == 700  # 1000 - 600 + (600 * 0.5)
    assert economy.get_balance(2) == 800  # 1000 - 400 + (400 * 0.5)
    assert economy.get_balance(3) == 500  # creator share
