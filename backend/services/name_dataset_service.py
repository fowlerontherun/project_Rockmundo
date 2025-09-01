"""Utility service for maintaining simple name datasets.

This module exposes helpers used by administrative endpoints to append new
first names or surnames to CSV files under ``backend/utils/data``.  The files
are created on demand and values are only appended when they do not already
exist in the corresponding dataset.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

# Base directory containing the CSV datasets
_DATA_DIR = Path(__file__).resolve().parents[1] / "utils" / "data"


def _append_unique(file_path: Path, name: str) -> bool:
    """Append ``name`` to ``file_path`` if it is not already present.

    Parameters
    ----------
    file_path:
        Path to the CSV file.
    name:
        The name to append.

    Returns
    -------
    bool
        ``True`` if the name was appended, ``False`` if it was already present.
    """

    # Ensure the data directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    normalised = name.strip()
    if not normalised:
        return False

    # Gather existing entries, if any
    existing: set[str] = set()
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as fh:
            existing = {line.strip().lower() for line in fh if line.strip()}

    if normalised.lower() in existing:
        return False

    with file_path.open("a", encoding="utf-8") as fh:
        fh.write(f"{normalised}\n")
    return True


def add_first_name(name: str, gender: Literal["male", "female"]) -> bool:
    """Add a first name to the gender specific dataset.

    Parameters
    ----------
    name:
        The first name to append.
    gender:
        ``"male"`` or ``"female"`` specifying which dataset to target.
    """

    file_map = {
        "male": _DATA_DIR / "male_names.csv",
        "female": _DATA_DIR / "female_names.csv",
    }
    return _append_unique(file_map[gender], name)


def add_surname(name: str) -> bool:
    """Add a surname to the dataset.

    Parameters
    ----------
    name:
        The surname to append.
    """

    return _append_unique(_DATA_DIR / "surnames.csv", name)
