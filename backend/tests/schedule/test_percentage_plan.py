from backend.services.plan_service import PlanService


def test_percentage_distribution():
    svc = PlanService()
    plan = svc.create_plan(social_pct=50, career_pct=25, band_pct=25)
    expected = [
        "network",
        "promote",
        "network",
        "promote",
        "practice",
        "songwriting",
        "rehearsal",
        "gig_prep",
    ]
    assert plan == expected


def test_percentage_rest_filled():
    svc = PlanService()
    plan = svc.create_plan(social_pct=25, career_pct=25, band_pct=0)
    assert plan[0:2] == ["network", "promote"]
    assert plan[2:4] == ["practice", "songwriting"]
    assert plan.count("rest") == svc.slots - 4
    assert len(plan) == svc.slots
