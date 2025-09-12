
from datetime import datetime

class Stream:
    def __init__(self, id, song_id, user_id, platform, timestamp=None):
        self.id = id
        self.song_id = song_id
        self.user_id = user_id
        self.platform = platform  # e.g., Spotify, YouTube, AppleMusic
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self):
        return self.__dict__
