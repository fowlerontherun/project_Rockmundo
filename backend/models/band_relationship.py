
from datetime import datetime
from random import randint


class BandRelationship:
    """Represents an inter-band relationship.

    Besides the type of relationship (``alliance`` or ``rivalry``) we track
    two additional statistics:

    ``affinity``
        How much the two bands like each other. Ranges 0-100 and defaults to a
        semi-random score around 50 when not specified.

    ``compatibility``
        Measures how well the bands work together. Also 0-100.  These values are
        later used by services to influence joint gig outcomes.
    """

    def __init__(
        self,
        id,
        band_a_id,
        band_b_id,
        type,
        since=None,
        active=True,
        affinity=None,
        compatibility=None,
    ):
        self.id = id
        self.band_a_id = band_a_id
        self.band_b_id = band_b_id
        self.type = type  # 'alliance' or 'rivalry'
        self.since = since or datetime.utcnow().isoformat()
        self.active = active
        # Default the stats to a pseudo-random neutral score if not provided
        self.affinity = affinity if affinity is not None else randint(40, 60)
        self.compatibility = (
            compatibility if compatibility is not None else randint(40, 60)
        )

    def to_dict(self):
        """Serialize the relationship to a dictionary."""
        return self.__dict__
