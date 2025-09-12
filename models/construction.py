from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class BuildPhase:
    """Represents one stage in a construction project."""

    name: str
    duration: int  # generic time units


@dataclass
class Blueprint:
    """A blueprint describing what to build on a parcel.

    ``target_type`` indicates which service should be updated when the build is
    completed.  Supported values are ``"property"`` and ``"venue"``.
    ``upgrade_effect`` is a simple mapping of field to value that will be passed
    to the corresponding service.  The interpretation of those fields is left to
    the service itself.
    """

    name: str
    cost: int
    phases: List[BuildPhase]
    target_type: str
    upgrade_effect: Dict[str, int]


@dataclass
class LandParcel:
    """Piece of land owned by a player on which buildings can be erected."""

    id: int
    owner_id: int
    location: str
    size: int


@dataclass
class ConstructionTask:
    """An entry in the build queue."""

    parcel_id: int
    blueprint: Blueprint
    owner_id: int
    target_id: int
    phase_index: int = 0
    remaining: int = field(init=False)
    prepaid_cost: int = 0

    def __post_init__(self) -> None:
        self.remaining = self.blueprint.phases[0].duration
