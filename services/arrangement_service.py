from __future__ import annotations

from typing import Dict, List, Optional

from models.arrangement import ArrangementTrack
from models.song import Song
from backend.services.recording_service import RecordingService, recording_service
from backend.models.arrangement import ArrangementTrack
from backend.models.song import Song
from services.recording_service import RecordingService, recording_service


class ArrangementService:
    """Manage arrangement tracks for songs and integrate with recording sessions."""

    def __init__(self, recording: Optional[RecordingService] = None) -> None:
        self.recording = recording or recording_service
        self._tracks: Dict[int, ArrangementTrack] = {}
        self._songs: Dict[int, Song] = {}
        self._id_seq = 1

    # CRUD operations -------------------------------------------------
    def add_track(
        self,
        song: Song,
        track_type: str,
        performer: Optional[str] = None,
        notes: str = "",
    ) -> ArrangementTrack:
        """Add a new arrangement track to a song."""

        track = ArrangementTrack(
            id=self._id_seq,
            song_id=song.id,
            track_type=track_type,
            performer=performer,
            notes=notes,
        )
        self._tracks[track.id] = track
        self._songs.setdefault(song.id, song).arrangement.append(track)
        self._id_seq += 1
        return track

    def get_track(self, track_id: int) -> Optional[ArrangementTrack]:
        return self._tracks.get(track_id)

    def list_tracks(self, song_id: int) -> List[ArrangementTrack]:
        song = self._songs.get(song_id)
        return list(song.arrangement) if song else []

    def update_track(
        self,
        track_id: int,
        *,
        track_type: Optional[str] = None,
        performer: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ArrangementTrack:
        track = self._tracks.get(track_id)
        if not track:
            raise KeyError("track_not_found")
        if track_type is not None:
            track.track_type = track_type
        if performer is not None:
            track.performer = performer
        if notes is not None:
            track.notes = notes
        return track

    def delete_track(self, track_id: int) -> None:
        track = self._tracks.pop(track_id, None)
        if not track:
            return
        song = self._songs.get(track.song_id)
        if song:
            song.arrangement = [t for t in song.arrangement if t.id != track_id]

    # Integration with recording sessions -----------------------------
    def schedule_recording_session(
        self,
        song_id: int,
        band_id: int,
        studio: str,
        start: str,
        end: str,
        cost_cents: int,
    ):
        """Schedule a recording session using a song's arrangement tracks."""

        tracks = [t.id for t in self.list_tracks(song_id)]
        return self.recording.schedule_session(
            band_id=band_id,
            studio=studio,
            start=start,
            end=end,
            tracks=tracks,
            cost_cents=cost_cents,
        )


arrangement_service = ArrangementService()

__all__ = ["ArrangementService", "arrangement_service"]
