from services import lifestyle_service


def _collect(monkeypatch):
    awarded = []

    def fake_grant(user_id, reason, amount, conn=None):
        awarded.append(amount)
        return True

    monkeypatch.setattr(lifestyle_service.xp_reward_service, "grant_hidden_xp", fake_grant)
    return awarded


def test_low_lifestyle_score_reduces_xp(monkeypatch):
    awarded = _collect(monkeypatch)

    low = {
        "sleep_hours": 4,
        "stress": 90,
        "training_discipline": 20,
        "mental_health": 40,
        "nutrition": 30,
        "fitness": 20,
    }
    high = {
        "sleep_hours": 8,
        "stress": 10,
        "training_discipline": 80,
        "mental_health": 90,
        "nutrition": 80,
        "fitness": 70,
    }

    lifestyle_service.grant_daily_xp(1, low)
    lifestyle_service.grant_daily_xp(1, high)

    assert awarded[0] < awarded[1]


def test_recovery_action_restores_xp(monkeypatch):
    awarded = _collect(monkeypatch)

    data = {
        "sleep_hours": 4,
        "stress": 90,
        "training_discipline": 20,
        "mental_health": 40,
        "nutrition": 30,
        "fitness": 20,
    }

    lifestyle_service.grant_daily_xp(1, data)
    before = awarded[-1]

    lifestyle_service.apply_recovery_action(1, data, "rest")
    lifestyle_service.grant_daily_xp(1, data)
    after = awarded[-1]

    assert after > before
