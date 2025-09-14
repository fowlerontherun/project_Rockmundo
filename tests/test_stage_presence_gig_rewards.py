import sqlite3

from services import gig_service as gs


def _setup_gig_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE gigs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            city TEXT,
            venue_size INTEGER,
            date TEXT,
            ticket_price INTEGER,
            status TEXT,
            attendance INTEGER,
            revenue INTEGER,
            fame_gain INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def test_stage_presence_boosts_gig_rewards(monkeypatch, tmp_path):
    db = tmp_path / "gig.db"
    _setup_gig_db(db)
    monkeypatch.setattr(gs, "DB_PATH", str(db))
    monkeypatch.setattr(
        gs.fan_service,
        "get_band_fan_stats",
        lambda _bid: {"total_fans": 200, "average_loyalty": 50},
    )
    fans = []

    def fake_boost(_bid, _city, attendance):
        fans.append(attendance // 10)

    monkeypatch.setattr(gs.fan_service, "boost_fans_after_gig", fake_boost)
    monkeypatch.setattr(gs.random, "randint", lambda a, b: 0)

    class DummyAvatar:
        def __init__(self, sp):
            self.stage_presence = sp

    class DummyAvatarService:
        def __init__(self, sp):
            self.sp = sp

        def get_avatar(self, _band_id):
            return DummyAvatar(self.sp)

    monkeypatch.setattr(gs, "avatar_service", DummyAvatarService(10))
    gs.create_gig(1, "Test City", 500, "2024-01-01", 10)
    res_low = gs.simulate_gig_result(1)
    fans_low = fans.pop()

    monkeypatch.setattr(gs, "avatar_service", DummyAvatarService(90))
    gs.create_gig(1, "Test City", 500, "2024-01-02", 10)
    res_high = gs.simulate_gig_result(2)
    fans_high = fans.pop()

    assert res_high["earnings"] > res_low["earnings"]
    assert fans_high > fans_low
