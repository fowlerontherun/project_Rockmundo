from dataclasses import dataclass, field
from typing import List


@dataclass
class Playlist:
    """Simple playlist model keeping track of songs."""

    id: int
    name: str
    song_ids: List[int] = field(default_factory=list)
    is_public: bool = False

    def add_song(self, song_id: int) -> None:
        """Add a song to the playlist if not already present."""
        if song_id not in self.song_ids:
            self.song_ids.append(song_id)

    def remove_song(self, song_id: int) -> None:
        """Remove a song from the playlist if it exists."""
        if song_id in self.song_ids:
            self.song_ids.remove(song_id)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "song_ids": self.song_ids,
            "is_public": self.is_public,
        }
