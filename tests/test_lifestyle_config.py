from backend.config import lifestyle as cfg
from services.lifestyle_scheduler import lifestyle_xp_modifier


def test_default_lifestyle_config_values() -> None:
    assert cfg.DECAY == {
        "mental_health": 1.0,
        "stress": 1.5,
        "training_discipline": 0.5,
    }
    assert cfg.MODIFIER_THRESHOLDS == {
        "sleep_hours": {"min": 5, "modifier": 0.7},
        "stress": {"max": 80, "modifier": 0.75},
        "training_discipline": {"min": 30, "modifier": 0.85},
        "mental_health": {"min": 60, "modifier": 0.8},
        "nutrition": {"min": 40, "modifier": 0.9},
        "fitness": {"min": 30, "modifier": 0.9},
    }


def test_modifier_respects_config() -> None:
    thresholds = cfg.MODIFIER_THRESHOLDS
    assert (
        lifestyle_xp_modifier(4, 20, 100, 100, 100, 100, thresholds)
        == thresholds["sleep_hours"]["modifier"]
    )
    assert (
        lifestyle_xp_modifier(8, 90, 100, 100, 100, 100, thresholds)
        == thresholds["stress"]["modifier"]
    )
    assert (
        lifestyle_xp_modifier(8, 20, 20, 100, 100, 100, thresholds)
        == thresholds["training_discipline"]["modifier"]
    )
    assert (
        lifestyle_xp_modifier(8, 20, 100, 50, 100, 100, thresholds)
        == thresholds["mental_health"]["modifier"]
    )
    assert (
        lifestyle_xp_modifier(8, 20, 100, 100, 30, 100, thresholds)
        == thresholds["nutrition"]["modifier"]
    )
    assert (
        lifestyle_xp_modifier(8, 20, 100, 100, 100, 20, thresholds)
        == thresholds["fitness"]["modifier"]
    )

