from __future__ import annotations

from typing import List


def mix_tracks(performance_ids: List[int]) -> List[int]:
    """Return identifiers for mixed audio tracks.

    In the real application this function would take raw performance
    recordings and produce mixed tracks stored in an audio service.  For test
    purposes we simply return deterministic identifiers derived from the
    provided ``performance_ids``.
    """

    # A simple deterministic transformation that is easy to assert in tests.
    return [pid + 1000 for pid in performance_ids]
