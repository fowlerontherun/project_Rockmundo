from models.payment import SubscriptionPlan


def test_subscription_plan_defaults():
    plan = SubscriptionPlan(id="basic", name="Basic", price_cents=100, currency="USD", interval="monthly")
    assert plan.benefits == []
