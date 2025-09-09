import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from backend.utils.metrics import Counter, _REGISTRY, generate_latest


def test_generate_latest_has_trailing_newline():
    _REGISTRY.clear()
    Counter("requests_total", "Number of requests").labels()
    data = generate_latest()
    assert data.endswith(b"\n")

