from seeds.skill_seed import SEED_SKILLS, SKILL_NAME_TO_ID


LUTHIERY_SKILLS = {
    "luthiery",
    "woodworking",
    "fretwork",
    "instrument_electronics",
    "instrument_finishing",
    "advanced_luthiery",
    "master_luthier",
    "legendary_luthier",
}


def _skill(name):
    return next(skill for skill in SEED_SKILLS if skill.name == name)


def test_luthiery_skills_are_present_and_append_only():
    # data_analytics was the final legacy seed skill before Luthiery.
    legacy_last_id = SKILL_NAME_TO_ID["data_analytics"]
    ids = [SKILL_NAME_TO_ID[name] for name in LUTHIERY_SKILLS]
    assert min(ids) > legacy_last_id
    assert len(ids) == len(set(ids))


def test_luthiery_specialist_unlocks():
    root = SKILL_NAME_TO_ID["luthiery"]
    assert _skill("woodworking").parent_id == root
    assert _skill("woodworking").prerequisites == {root: 20}
    assert _skill("fretwork").prerequisites == {root: 30}
    assert _skill("instrument_electronics").prerequisites == {root: 40}
    assert _skill("instrument_finishing").prerequisites == {root: 40}


def test_advanced_master_and_legendary_unlock_chain():
    advanced = _skill("advanced_luthiery")
    assert advanced.prerequisites == {
        SKILL_NAME_TO_ID["luthiery"]: 50,
        SKILL_NAME_TO_ID["woodworking"]: 20,
        SKILL_NAME_TO_ID["fretwork"]: 20,
    }
    master = _skill("master_luthier")
    assert master.parent_id == SKILL_NAME_TO_ID["advanced_luthiery"]
    assert master.prerequisites == {SKILL_NAME_TO_ID["advanced_luthiery"]: 75}
    legendary = _skill("legendary_luthier")
    assert legendary.parent_id == SKILL_NAME_TO_ID["master_luthier"]
    assert legendary.prerequisites == {SKILL_NAME_TO_ID["master_luthier"]: 100}
