import sqlite3

from backend.services.stream_service import StreamService
from backend.services import fan_service


class DummyDB:
    def __init__(self):
        self.revenues = []
        self.song = {"royalties_split": {1: 100}}

    def insert_stream(self, stream):
        pass

    def get_song_by_id(self, song_id):
        return self.song

    def add_revenue_entry(self, band_id, song_id, revenue, timestamp):
        self.revenues.append(revenue)

    def get_revenue_by_band(self, band_id):  # pragma: no cover - not used
        return self.revenues

    def get_streams_by_song(self, song_id):  # pragma: no cover - not used
        return []


class DummyAvatar:
    def __init__(self, charisma: int = 50, social_media: int = 0):
        self.charisma = charisma
        self.social_media = social_media


class DummyAvatarService:
    def __init__(self, social_media: int):
        self.avatar = DummyAvatar(social_media=social_media)

    def get_avatar(self, _band_id):
        return self.avatar


class DummySkillService:
    def train(self, band_id, skill, amount):
        skill.level = 1
        return skill


def test_social_media_boosts_streaming_revenue():
    db_low = DummyDB()
    db_high = DummyDB()
    svc_low = StreamService(db_low, avatar_service=DummyAvatarService(0))
    svc_high = StreamService(db_high, avatar_service=DummyAvatarService(80))
    data = {"id": 1, "song_id": 1, "user_id": 1, "platform": "Spotify"}
    svc_low.record_stream(data)
    svc_high.record_stream(data)
    assert db_high.revenues[0] > db_low.revenues[0]


def test_social_media_increases_fan_conversions(tmp_path, monkeypatch):
    db_file = tmp_path / "fans.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE fans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            band_id INTEGER,
            location TEXT,
            loyalty INTEGER,
            source TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(fan_service, "DB_PATH", db_file)
    monkeypatch.setattr(fan_service, "skill_service", DummySkillService())

    monkeypatch.setattr(fan_service, "avatar_service", DummyAvatarService(0))
    low = fan_service.boost_fans_after_gig(1, "NY", 100)

    monkeypatch.setattr(fan_service, "avatar_service", DummyAvatarService(80))
    high = fan_service.boost_fans_after_gig(1, "NY", 100)

    assert high["fans_boosted"] > low["fans_boosted"]
