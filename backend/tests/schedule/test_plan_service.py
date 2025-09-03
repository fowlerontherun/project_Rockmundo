from backend.services.plan_service import PlanService


def test_category_mapping():
    svc = PlanService()
    plan = svc.create_plan(social=True, career=True, band=False)
    expected = PlanService.CATEGORY_MAP["social"] + PlanService.CATEGORY_MAP["career"]
    assert plan[: len(expected)] == expected


def test_rest_insertion():
    svc = PlanService()
    plan = svc.create_plan(social=True, career=False, band=False)
    # first entries from social category
    assert plan[0:2] == PlanService.CATEGORY_MAP["social"]
    # rest fills remaining slots
    assert plan.count("rest") == svc.slots - len(PlanService.CATEGORY_MAP["social"])
    assert len(plan) == svc.slots
    assert plan[-1] == "rest"
