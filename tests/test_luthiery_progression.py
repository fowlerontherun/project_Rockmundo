from services.luthiery_progression import (
    LEARNING_OPTIONS,
    SKILL_DESCRIPTIONS,
    UNLOCKS,
    learning_options_for,
    unlocks_for_level,
)


EXPECTED_SKILLS = {
    "luthiery",
    "woodworking",
    "fretwork",
    "instrument_electronics",
    "instrument_finishing",
    "advanced_luthiery",
    "master_luthier",
    "legendary_luthier",
}


def test_every_luthiery_skill_has_description_and_learning_route():
    assert set(SKILL_DESCRIPTIONS) == EXPECTED_SKILLS
    for skill in EXPECTED_SKILLS:
        assert learning_options_for(skill), f"{skill} has no learning route"


def test_required_learning_methods_are_available():
    methods = {option.method for option in LEARNING_OPTIONS}
    assert {"book", "university", "youtube", "tutor"} <= methods


def test_progression_has_all_reward_categories_and_upcoming_items():
    assert set(UNLOCKS) == {"materials", "shapes", "finishes", "components"}
    level_one = unlocks_for_level(1)
    for category in UNLOCKS:
        assert level_one[category]["unlocked"]
        assert level_one[category]["upcoming"]


def test_unlocks_are_monotonic_and_stable_keys_unique():
    keys = set()
    for rows in UNLOCKS.values():
        levels = [level for level, _key, _name in rows]
        assert levels == sorted(levels)
        for _level, key, _name in rows:
            assert key.startswith("luthier.")
            assert key not in keys
            keys.add(key)
