import random

from backend.services.random_event_service import RandomEventService


def run_trials(service, luck: int, iterations: int = 1000) -> int:
    options = [
        {"type": "good", "description": "", "impact": {"fame": 5}},
        {"type": "bad", "description": "", "impact": {"fame": -5}},
    ]
    good = 0
    for _ in range(iterations):
        event = service._trigger(None, 1, None, options, luck=luck)
        if event["type"] == "good":
            good += 1
    return good


def test_high_luck_increases_positive_events():
    random.seed(0)
    service = RandomEventService(db=None)
    low = run_trials(service, luck=0)
    high = run_trials(service, luck=80)
    assert high > low
