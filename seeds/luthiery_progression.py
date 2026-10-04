"""Canonical Luthiery progression metadata.

This module is deliberately data-only. Skill UI, learning discovery and later
crafting phases consume the same definitions so unlock rules cannot drift.
"""

from __future__ import annotations

LUTHIERY_SKILL_META = {
    "luthiery": {"label": "Luthiery", "tier": "basic", "description": "Design, build and maintain stringed instruments."},
    "woodworking": {"label": "Woodworking", "tier": "specialist", "description": "Improves body and neck construction and unlocks advanced woods."},
    "fretwork": {"label": "Fretwork", "tier": "specialist", "description": "Improves fretboards, setup accuracy and playability."},
    "instrument_electronics": {"label": "Instrument Electronics", "tier": "specialist", "description": "Unlocks pickups, wiring and advanced electronic configurations."},
    "instrument_finishing": {"label": "Instrument Finishing", "tier": "specialist", "description": "Unlocks premium colours, finishes and higher finish quality."},
    "advanced_luthiery": {"label": "Advanced Luthiery", "tier": "professional", "description": "Combines specialist disciplines into professional instrument building."},
    "master_luthier": {"label": "Master Luthier", "tier": "mastery", "description": "Unlocks master-grade construction choices and shapes."},
    "legendary_luthier": {"label": "Legendary Luthier", "tier": "legendary", "description": "Unlocks RockMundo's rarest signature construction options."},
}

# Each skill has at least one concrete learning route.
LUTHIERY_LEARNING_PATHS = {
    "luthiery": ("book", "youtube", "course", "tutor"),
    "woodworking": ("book", "course", "tutor"),
    "fretwork": ("book", "course", "tutor"),
    "instrument_electronics": ("book", "youtube", "course", "tutor"),
    "instrument_finishing": ("book", "youtube", "course", "tutor"),
    "advanced_luthiery": ("book", "course", "tutor"),
    "master_luthier": ("course", "tutor"),
    "legendary_luthier": ("tutor",),
}

LUTHIERY_BOOKS = (
    {"title": "Luthiery: First Build", "skill": "luthiery", "tier": "beginner", "max_skill_level": 20},
    {"title": "Working Woods for Instruments", "skill": "woodworking", "tier": "intermediate", "max_skill_level": 60},
    {"title": "Precision Fretwork", "skill": "fretwork", "tier": "intermediate", "max_skill_level": 60},
    {"title": "Electric Instrument Circuits", "skill": "instrument_electronics", "tier": "intermediate", "max_skill_level": 60},
    {"title": "Instrument Finishes and Colour", "skill": "instrument_finishing", "tier": "intermediate", "max_skill_level": 60},
    {"title": "Advanced Luthiery", "skill": "advanced_luthiery", "tier": "advanced", "max_skill_level": 100},
)

LUTHIERY_COURSES = (
    {"title": "Foundation Luthiery", "skill": "luthiery", "min_level": 1},
    {"title": "Instrument Woodworking", "skill": "woodworking", "min_level": 1},
    {"title": "Professional Fretwork", "skill": "fretwork", "min_level": 1},
    {"title": "Pickup and Wiring Design", "skill": "instrument_electronics", "min_level": 1},
    {"title": "Professional Instrument Finishing", "skill": "instrument_finishing", "min_level": 1},
    {"title": "Advanced Instrument Construction", "skill": "advanced_luthiery", "min_level": 1},
    {"title": "Master Luthier Workshop", "skill": "master_luthier", "min_level": 1},
)

LUTHIERY_VIDEOS = (
    {"title": "Your First Electric Guitar Build", "skill": "luthiery", "plateau_level": 10},
    {"title": "Pickup Wiring Basics", "skill": "instrument_electronics", "plateau_level": 20},
    {"title": "Spray and Polish Fundamentals", "skill": "instrument_finishing", "plateau_level": 20},
)

LUTHIERY_TUTORS = (
    {"name": "Workshop Luthier", "skill": "luthiery", "level_requirement": 15},
    {"name": "Woodcraft Specialist", "skill": "woodworking", "level_requirement": 15},
    {"name": "Fret Technician", "skill": "fretwork", "level_requirement": 15},
    {"name": "Instrument Electronics Technician", "skill": "instrument_electronics", "level_requirement": 15},
    {"name": "Finish Specialist", "skill": "instrument_finishing", "level_requirement": 15},
    {"name": "Professional Luthier", "skill": "advanced_luthiery", "level_requirement": 25},
    {"name": "Master Luthier", "skill": "master_luthier", "level_requirement": 25},
    {"name": "Legendary Builder", "skill": "legendary_luthier", "level_requirement": 25},
)

# Rewards use stable content keys defined by Phase 0.
LUTHIERY_UNLOCKS = {
    "materials": (
        (1, ("luthier.material.basswood", "luthier.material.poplar", "luthier.material.maple", "luthier.material.rosewood")),
        (20, ("luthier.material.alder", "luthier.material.ash")),
        (40, ("luthier.material.mahogany", "luthier.material.walnut", "luthier.material.ebony")),
        (70, ("luthier.material.flame_maple", "luthier.material.quilted_maple")),
        (100, ("luthier.material.exotic_premium", "luthier.material.carbon_reinforcement")),
    ),
    "shapes": (
        (1, ("luthier.shape.guitar.s_style", "luthier.shape.guitar.t_style", "luthier.shape.bass.p_style", "luthier.shape.bass.j_style")),
        (30, ("luthier.shape.guitar.single_cut", "luthier.shape.guitar.double_cut")),
        (50, ("luthier.shape.guitar.v", "luthier.shape.guitar.explorer", "luthier.shape.guitar.offset")),
        (75, ("luthier.shape.guitar.headless", "luthier.shape.guitar.semi_hollow", "luthier.shape.guitar.extended_range")),
        (100, ("luthier.shape.guitar.extreme_asymmetric", "luthier.shape.guitar.coffin", "luthier.shape.guitar.star")),
    ),
    "finishes": (
        (1, ("luthier.finish.solid", "luthier.finish.natural")),
        (25, ("luthier.finish.transparent", "luthier.finish.gloss")),
        (50, ("luthier.finish.matte", "luthier.finish.metallic")),
        (80, ("luthier.finish.premium_burst",)),
    ),
    "components": (
        (1, ("luthier.component.electronics.ceramic", "luthier.component.hardware.standard")),
        (25, ("luthier.component.electronics.alnico", "luthier.component.hardware.tremolo")),
        (50, ("luthier.component.electronics.active", "luthier.component.hardware.locking_tuners")),
        (75, ("luthier.component.electronics.boutique", "luthier.component.hardware.brass")),
        (100, ("luthier.component.hardware.titanium",)),
    ),
}


def unlocked_rewards(level: int) -> dict[str, list[str]]:
    return {kind: [key for required, keys in rows if level >= required for key in keys] for kind, rows in LUTHIERY_UNLOCKS.items()}


def upcoming_rewards(level: int) -> dict[str, dict | None]:
    result = {}
    for kind, rows in LUTHIERY_UNLOCKS.items():
        next_row = next(((required, keys) for required, keys in rows if required > level), None)
        result[kind] = None if next_row is None else {"level": next_row[0], "keys": list(next_row[1])}
    return result
