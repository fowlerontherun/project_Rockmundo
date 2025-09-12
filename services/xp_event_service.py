"""Service layer for managing XP boost events."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from models.xp_event import XPEvent


class XPEventService:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(__file__).resolve().parents[1] / "xp_events.json"
        self._events: List[XPEvent] = self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    def _load(self) -> List[XPEvent]:
        if self.path.exists():
            data = json.loads(self.path.read_text())
            return [XPEvent.from_dict(e) for e in data]
        return []

    def _save(self) -> None:
        data = [e.to_dict() for e in self._events]
        self.path.write_text(json.dumps(data))

    # ------------------------------------------------------------------
    # CRUD operations
    def list_events(self) -> List[XPEvent]:
        return list(self._events)

    def create_event(self, event: XPEvent) -> XPEvent:
        next_id = max((e.id or 0 for e in self._events), default=0) + 1
        event.id = next_id
        self._events.append(event)
        self._save()
        return event

    def update_event(self, event_id: int, **changes) -> XPEvent:
        ev = self.get_event(event_id)
        if ev is None:
            raise ValueError("Event not found")
        for k, v in changes.items():
            if hasattr(ev, k) and v is not None:
                setattr(ev, k, v)
        self._save()
        return ev

    def delete_event(self, event_id: int) -> None:
        self._events = [e for e in self._events if e.id != event_id]
        self._save()

    def get_event(self, event_id: int) -> Optional[XPEvent]:
        return next((e for e in self._events if e.id == event_id), None)

    # ------------------------------------------------------------------
    # Event lookup
    def get_active_events(self, skill: str | None = None) -> List[XPEvent]:
        now = datetime.utcnow()
        return [
            e
            for e in self._events
            if e.start_time <= now <= e.end_time
            and (e.skill_target is None or e.skill_target == skill)
        ]

    def get_active_multiplier(self, skill: str | None = None) -> float:
        mult = 1.0
        for e in self.get_active_events(skill):
            mult += e.multiplier - 1
        return mult
