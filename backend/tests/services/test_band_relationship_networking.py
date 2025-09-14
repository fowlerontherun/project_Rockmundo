import pytest
from services.band_relationship_service import BandRelationshipService


def test_high_profile_collab_requires_networking():
    svc = BandRelationshipService()
    # low networking should block
    with pytest.raises(ValueError):
        svc.create_relationship(1, 2, "collab", high_profile=True, networking=30)
    # high networking should allow
    rel = svc.create_relationship(1, 2, "collab", high_profile=True, networking=80)
    assert rel["band_a_id"] == 1 and rel["band_b_id"] == 2
