from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict


@dataclass
class AdminSession:
    """Represents a short-lived admin session verified via MFA."""

    id: str
    device: str
    ip: str
    code: str
    expires_at: datetime
    verified: bool = False

    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.expires_at


# In-memory store of admin sessions. In a real application this would live in a
# database or shared cache, but for the purposes of tests an in-memory dict is
# sufficient.
admin_sessions: Dict[str, AdminSession] = {}
