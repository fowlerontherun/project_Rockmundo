import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE))
sys.path.append(str(BASE / "backend"))

from backend.seeds.skill_seed import SKILL_NAME_TO_ID  # noqa: E402


def test_skill_name_to_id_unique_values():
    values = list(SKILL_NAME_TO_ID.values())
    assert len(values) == len(set(values))
