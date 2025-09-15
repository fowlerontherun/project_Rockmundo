"""Media placement service and influencer collaborations."""

from __future__ import annotations

from typing import Dict, List

from models.influencer_models import Collaboration, CollaborationStatus

from services.song_popularity_service import add_event


def record_media_placement(song_id: int, placement_type: str) -> None:
    """Record that a song was placed in some media and boost its popularity.

    Args:
        song_id: The song receiving placement.
        placement_type: e.g. "film", "tv", "ad".
    """
    boost = 20.0 if placement_type.lower() == "film" else 10.0
    add_event(song_id, boost, placement_type)


_collaborations: Dict[int, Collaboration] = {}
_next_collab_id = 1


def request_collaboration(
    initiator_id: int, partner_id: int, details: str | None = None
) -> Collaboration:
    """Initiate a collaboration request between influencers."""

    global _next_collab_id
    collab = Collaboration(
        id=_next_collab_id,
        initiator_id=initiator_id,
        partner_id=partner_id,
        details=details,
    )
    _collaborations[_next_collab_id] = collab
    _next_collab_id += 1
    return collab


def respond_to_collaboration(collab_id: int, accept: bool) -> Collaboration:
    """Accept or reject a collaboration request."""

    collab = _collaborations.get(collab_id)
    if not collab:
        raise KeyError("Collaboration not found")
    collab.status = (
        CollaborationStatus.ACCEPTED if accept else CollaborationStatus.REJECTED
    )
    return collab


def list_collaborations(influencer_id: int) -> List[Collaboration]:
    """Return collaborations for the given influencer."""

    return [
        c
        for c in _collaborations.values()
        if c.initiator_id == influencer_id or c.partner_id == influencer_id
    ]
