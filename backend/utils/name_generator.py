"""Utilities for generating character names.

This module loads male and female first-name pools along with a
gender-neutral surname pool from CSV files located in the sibling
``data`` directory.  Names can then be generated for a requested gender
and optionally decorated with stage-style suffixes or aliases.
"""

from __future__ import annotations

import csv
import random
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


# === Load name pools from CSV files ========================================

DATA_DIR = Path(__file__).with_suffix("").parent / "data"


def _load_names(filename: str) -> List[str]:
    """Return a list of names loaded from ``filename``.

    Each line in the CSV is treated as a single name.  Missing files are
    tolerated and simply result in an empty list.
    """

    path = DATA_DIR / filename
    try:
        with path.open(newline="", encoding="utf-8") as f:
            return [row[0].strip() for row in csv.reader(f) if row]
    except FileNotFoundError:
        return []


MALE_FIRST_NAMES = _load_names("male_names.csv")
FEMALE_FIRST_NAMES = _load_names("female_names.csv")
LAST_NAMES = _load_names("surnames.csv")


def reload_name_pools() -> None:
    """Reload name pools from CSV files into module-level lists."""

    global MALE_FIRST_NAMES, FEMALE_FIRST_NAMES, LAST_NAMES
    MALE_FIRST_NAMES = _load_names("male_names.csv")
    FEMALE_FIRST_NAMES = _load_names("female_names.csv")
    LAST_NAMES = _load_names("surnames.csv")


def append_name(gender: str | None, name: str) -> None:
    """Append ``name`` to the appropriate pool and update in-memory lists.

    Parameters
    ----------
    gender:
        ``"male"`` or ``"female"`` appends to the respective first-name pool.
        ``None`` appends to the surname pool.
    name:
        The name to add.
    """

    mapping = {
        "male": ("male_names.csv", MALE_FIRST_NAMES),
        "female": ("female_names.csv", FEMALE_FIRST_NAMES),
        None: ("surnames.csv", LAST_NAMES),
    }
    if gender not in mapping:
        raise ValueError("gender must be 'male', 'female', or None")

    filename, target = mapping[gender]
    path = DATA_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([name])
    target.append(name.strip())


# === Static stage/alias data ===============================================

STAGE_SUFFIXES = [
    "the Great",
    "X",
    "5000",
    "Deluxe",
    "of Doom",
    "Junior",
    "III",
]

ALIAS_NAMES = [
    "Roxette",
    "Zephyr",
    "Electra",
    "Nova",
    "Phantom",
    "Blaze",
    "Echo",
    "Shadow",
    "Riot",
    "Storm",
]


DB_PATH = "devmind_schema.db"


def is_name_taken(name: str) -> bool:
    """Return ``True`` if ``name`` exists in the ``characters`` table."""

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM characters WHERE name = ?", (name,))
        taken = cur.fetchone()[0] > 0
        conn.close()
        return taken
    except Exception:
        return False


def _choose_first_name(gender: Optional[str]) -> str:
    """Select a first name from the gender-specific pools."""

    if gender == "male":
        pool = MALE_FIRST_NAMES
    elif gender == "female":
        pool = FEMALE_FIRST_NAMES
    else:
        pool = MALE_FIRST_NAMES + FEMALE_FIRST_NAMES

    if not pool:
        raise ValueError("First-name pools are empty")

    return random.choice(pool)


def generate_random_name(style: str = "full", gender: Optional[str] = None) -> str:
    """Generate a random name.

    Args:
        style: ``"full"`` (default) returns ``first last``.
               ``"suffix"`` appends a stage suffix.
               ``"alias"`` returns an alias independent of gender.
        gender: ``"male"`` or ``"female"`` restricts the first-name pool.
                ``None`` chooses from both pools.
    """

    if style == "alias":
        return random.choice(ALIAS_NAMES)

    first_name = _choose_first_name(gender)
    last_name = random.choice(LAST_NAMES) if LAST_NAMES else ""
    base = f"{first_name} {last_name}".strip()

    if style == "suffix":
        return f"{base} {random.choice(STAGE_SUFFIXES)}".strip()

    return base


def generate_unique_names(
    n: int = 10, style: str = "full", gender: Optional[str] = None
) -> List[str]:
    """Generate ``n`` unique names, avoiding duplicates and taken names."""

    names = set()
    attempts = 0
    while len(names) < n and attempts < 2000:
        name = generate_random_name(style=style, gender=gender)
        if name not in names and not is_name_taken(name):
            names.add(name)
        attempts += 1
    return list(names)


def get_name_choices() -> Dict[str, List[str]]:
    """Return a set of name choices for the front-end selector."""

    return {
        "standard": generate_unique_names(10, style="full"),
        "stage_suffix": generate_unique_names(10, style="suffix"),
        "alias": generate_unique_names(10, style="alias"),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(get_name_choices(), indent=2))

