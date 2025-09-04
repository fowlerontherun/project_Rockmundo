"""Seed the development database with demo data."""

from __future__ import annotations

import sqlite3
import sys
from importlib import import_module
from pathlib import Path

# Ensure project root and backend package are on path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend.core.config import settings  # noqa: E402

SEEDS_DIR = ROOT / "backend" / "seeds"


def run_sql_seed(conn: sqlite3.Connection) -> None:
    sql_file = SEEDS_DIR / "demo_data.sql"
    if sql_file.exists():
        conn.executescript(sql_file.read_text(encoding="utf-8"))
        print(f"Loaded SQL seed data from {sql_file}")


def run_python_seeds(conn: sqlite3.Connection) -> None:
    for path in SEEDS_DIR.glob("*.py"):
        if path.name.startswith("__"):
            continue
        module = import_module(f"backend.seeds.{path.stem}")
        seed_fn = getattr(module, "seed", None)
        if callable(seed_fn):
            print(f"Running seed from {path.name}")
            seed_fn(conn)


def main() -> None:
    db_path = Path(settings.database.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        if (SEEDS_DIR / "demo_data.sql").exists():
            run_sql_seed(conn)
        else:
            run_python_seeds(conn)
    print("Database seeded with demo data.")


if __name__ == "__main__":  # pragma: no cover - utility script
    main()
