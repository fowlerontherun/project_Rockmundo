"""Service layer for music production workflows."""

from __future__ import annotations

from typing import Dict, List, Optional

from models.production import (
    MixingSession,
    ReleaseMetadata,
    StudioSession,
    Track,
)


class ProductionService:
    """Orchestrates recording, mixing and release of tracks."""

    def __init__(self, economy_service=None, analytics_service=None):
        self.economy = economy_service
        self.analytics = analytics_service
        self.tracks: Dict[int, Track] = {}
        self.sessions: Dict[int, StudioSession] = {}
        self.mixes: Dict[int, MixingSession] = {}
        self._next_track_id = 1
        self._next_session_id = 1
        self._next_mix_id = 1

    # ------------------ track lifecycle ------------------
    def create_track(self, title: str, band_id: int, duration_sec: int) -> Track:
        track = Track(self._next_track_id, title, band_id, duration_sec)
        self.tracks[track.id] = track
        self._next_track_id += 1
        return track

    def schedule_session(
        self,
        track_id: int,
        scheduled_date: str,
        engineer: str,
        hours: int,
        hourly_rate_cents: int,
    ) -> StudioSession:
        cost = hours * hourly_rate_cents
        session = StudioSession(
            self._next_session_id, track_id, scheduled_date, engineer, cost
        )
        self.sessions[session.id] = session
        self.tracks[track_id].sessions.append(session.id)
        self._next_session_id += 1
        return session

    def mix_track(
        self, track_id: int, engineer: str, cost_cents: int, mastered: bool = True
    ) -> MixingSession:
        mix = MixingSession(self._next_mix_id, track_id, engineer, cost_cents, mastered)
        self.mixes[mix.id] = mix
        self.tracks[track_id].mixing_id = mix.id
        self._next_mix_id += 1
        return mix

    def production_cost(self, track_id: int) -> int:
        track = self.tracks[track_id]
        total = sum(self.sessions[sid].cost_cents for sid in track.sessions)
        if track.mixing_id:
            total += self.mixes[track.mixing_id].cost_cents
        return total

    def release_track(
        self,
        track_id: int,
        release_date: str,
        channels: List[str],
        price_cents: int,
        sales: int,
    ) -> ReleaseMetadata:
        track = self.tracks[track_id]
        release = ReleaseMetadata(track_id, release_date, channels, sales)
        track.release = release

        revenue = price_cents * sales
        if self.economy is not None:
            # deposit revenue into band's account
            self.economy.deposit(track.band_id, revenue)
        if self.analytics is not None:
            if hasattr(self.analytics, "record_sale"):
                self.analytics.record_sale(track_id, sales)
            if hasattr(self.analytics, "update_charts"):
                self.analytics.update_charts(track_id, sales)
        return release

    def get_track(self, track_id: int) -> Optional[Track]:
        return self.tracks.get(track_id)

