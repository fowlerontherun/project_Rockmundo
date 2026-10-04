"""Authoritative Phase 1 Luthiery progression and learning catalogue.

These stable string keys are intentionally independent of positional skill IDs.
Later crafting phases should consume these unlock rules instead of duplicating
level checks in routes or UI code.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningOption:
    method: str
    title: str
    skill: str
    min_level: int = 1
    max_level: int | None = None


SKILL_DESCRIPTIONS = {
    "luthiery": "Build, set up and improve stringed instruments. Higher levels unlock better materials, shapes, finishes and component choices.",
    "woodworking": "Shape bodies and necks accurately. Improves structural quality and access to advanced woods.",
    "fretwork": "Install, level and finish frets and fretboards for better playability and intonation.",
    "instrument_electronics": "Wire pickups and controls. Unlocks stronger and more specialised electronic configurations.",
    "instrument_finishing": "Apply colour, stains and protective finishes with fewer cosmetic defects.",
    "advanced_luthiery": "Professional instrument construction combining specialist disciplines and advanced designs.",
    "master_luthier": "Master-level construction with premium components, difficult shapes and consistently high quality.",
    "legendary_luthier": "The pinnacle of the profession, unlocking RockMundo's rarest signature designs and materials.",
}

# UI-facing progression rewards. Phase 2 will map these stable keys to persistent
# material/component catalogue rows.
UNLOCKS = {
    "materials": [
        (1, "luthier.material.basswood", "Basswood"),
        (1, "luthier.material.poplar", "Poplar"),
        (10, "luthier.material.maple", "Maple"),
        (20, "luthier.material.rosewood", "Rosewood"),
        (30, "luthier.material.alder", "Alder"),
        (40, "luthier.material.ash", "Ash"),
        (50, "luthier.material.mahogany", "Mahogany"),
        (60, "luthier.material.walnut", "Walnut"),
        (70, "luthier.material.ebony", "Ebony"),
        (80, "luthier.material.flame_maple", "Flame Maple"),
        (90, "luthier.material.quilted_maple", "Quilted Maple"),
        (100, "luthier.material.premium_exotic", "Premium Exotic Woods"),
    ],
    "shapes": [
        (1, "luthier.shape.guitar.double_cut", "Double Cut"),
        (1, "luthier.shape.bass.p_style", "P-Style Bass"),
        (10, "luthier.shape.guitar.s_style", "S-Style"),
        (20, "luthier.shape.guitar.t_style", "T-Style"),
        (30, "luthier.shape.bass.j_style", "J-Style Bass"),
        (40, "luthier.shape.guitar.single_cut", "Single Cut"),
        (50, "luthier.shape.guitar.offset", "Offset"),
        (60, "luthier.shape.guitar.v", "V"),
        (70, "luthier.shape.guitar.explorer", "Explorer"),
        (80, "luthier.shape.guitar.modern_metal", "Modern Metal"),
        (90, "luthier.shape.guitar.headless", "Headless"),
        (100, "luthier.shape.guitar.signature_extreme", "Signature Extreme"),
    ],
    "finishes": [
        (1, "luthier.finish.solid", "Solid Colour"),
        (15, "luthier.finish.natural", "Natural"),
        (30, "luthier.finish.transparent", "Transparent"),
        (45, "luthier.finish.matte", "Matte"),
        (60, "luthier.finish.metallic", "Metallic"),
        (80, "luthier.finish.burst", "Burst"),
        (100, "luthier.finish.signature", "Signature Finish"),
    ],
    "components": [
        (1, "luthier.component.electronics.ceramic", "Ceramic Electronics"),
        (1, "luthier.component.hardware.standard", "Standard Hardware"),
        (20, "luthier.component.electronics.single_coil", "Single-Coil"),
        (30, "luthier.component.electronics.humbucker", "Humbucker"),
        (40, "luthier.component.electronics.alnico", "Alnico Electronics"),
        (50, "luthier.component.hardware.locking_tuners", "Locking Tuners"),
        (60, "luthier.component.electronics.active", "Active Electronics"),
        (70, "luthier.component.hardware.brass", "Brass Hardware"),
        (80, "luthier.component.electronics.boutique", "Boutique Electronics"),
        (90, "luthier.component.hardware.lightweight_premium", "Lightweight Premium Hardware"),
        (100, "luthier.component.hardware.master", "Master-Grade Hardware"),
    ],
}

LEARNING_OPTIONS = [
    LearningOption("book", "Luthiery: First Builds", "luthiery", 1, 20),
    LearningOption("youtube", "Workbench Basics: Guitar Building", "luthiery", 1, 10),
    LearningOption("apprenticeship", "Luthier Workshop Apprenticeship", "luthiery", 10),
    LearningOption("university", "Instrument Construction", "luthiery", 20),
    LearningOption("tutor", "Private Luthier Tuition", "luthiery", 15),
    LearningOption("book", "Practical Woodworking for Luthiers", "woodworking", 1, 20),
    LearningOption("workshop", "Advanced Tonewood Workshop", "woodworking", 25),
    LearningOption("book", "Fretwork and Setup", "fretwork", 1, 20),
    LearningOption("tutor", "Precision Fretwork Tuition", "fretwork", 15),
    LearningOption("youtube", "Pickup Wiring Fundamentals", "instrument_electronics", 1, 10),
    LearningOption("university", "Instrument Electronics", "instrument_electronics", 20),
    LearningOption("book", "Instrument Finishing Fundamentals", "instrument_finishing", 1, 20),
    LearningOption("workshop", "Professional Instrument Finishing", "instrument_finishing", 25),
    LearningOption("apprenticeship", "Advanced Luthier Apprenticeship", "advanced_luthiery", 10),
    LearningOption("tutor", "Master Builder Coaching", "advanced_luthiery", 15),
    LearningOption("tutor", "Master Luthier Mentorship", "master_luthier", 15),
    LearningOption("tutor", "Legendary Builder Mentorship", "legendary_luthier", 15),
]


def unlocks_for_level(level: int) -> dict[str, dict[str, list[dict[str, object]]]]:
    """Return unlocked and upcoming rewards for a Luthiery level."""

    result = {}
    for category, rows in UNLOCKS.items():
        unlocked = [
            {"level": req, "key": key, "name": name}
            for req, key, name in rows
            if req <= level
        ]
        upcoming = [
            {"level": req, "key": key, "name": name}
            for req, key, name in rows
            if req > level
        ]
        result[category] = {"unlocked": unlocked, "upcoming": upcoming}
    return result


def learning_options_for(skill: str) -> list[LearningOption]:
    return [option for option in LEARNING_OPTIONS if option.skill == skill]


__all__ = [
    "LearningOption",
    "SKILL_DESCRIPTIONS",
    "UNLOCKS",
    "LEARNING_OPTIONS",
    "unlocks_for_level",
    "learning_options_for",
]
