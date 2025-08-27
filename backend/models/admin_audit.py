from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AdminAudit:
    actor: int | None
    action: str
    resource: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "timestamp": self.timestamp,
        }
