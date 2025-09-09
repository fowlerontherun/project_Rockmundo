"""Tests for the skill service."""

# ruff: noqa: E402
import sqlite3
import sys
import types
from pathlib import Path
import time

import pytest

sys.modules.setdefault(
    "backend.services.notifications_service",
    types.SimpleNamespace(NotificationsService=object),
)
sys.modules.setdefault(
    "services.xp_reward_service", types.SimpleNamespace(xp_reward_service=object)
)


class DummyAvatarService:
    def __init__(self):
        self.updates: list[tuple[int, object]] = []

    def get_avatar(self, user_id: int):  # pragma: no cover - simple stub
        return types.SimpleNamespace(
            charisma=0,
            creativity=0,
            intelligence=0,
            discipline=50,
            stamina=100,
            fatigue=0,
            voice=0,
        )

    def update_avatar(self, user_id: int, update):  # pragma: no cover - simple tracking
        self.updates.append((user_id, update))


sys.modules["backend.services.avatar_service"] = types.SimpleNamespace(
    AvatarService=DummyAvatarService
)

from backend.models.item import Item
from backend.models.learning_method import LearningMethod
from backend.models.skill import Skill, SkillSpecialization
from backend.models.xp_config import XPConfig, get_config, set_config
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services.skill_service import SkillService
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services.vocal_training_service import VocalTrainingService
from backend.services.recording_service import RecordingService
item_service = None  # set in _setup_device


class DummyXPEvents:
    def __init__(self, mult: float):
        self.mult = mult

    def get_active_multiplier(self, skill: str | None = None) -> float:  # pragma: no cover - simple proxy
        return self.mult


def _setup_db(
    tmp_path: Path,
    xp_modifier: float = 1.0,
    lifestyle: tuple[float, float, float, float, float, float] = (7, 0, 50, 100, 70, 70),
    learning_style: str = "balanced",
) -> Path:
    db = tmp_path / "db.sqlite"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE xp_modifiers (user_id INTEGER, modifier REAL, date TEXT)"
    )
    cur.execute(
        "INSERT INTO xp_modifiers (user_id, modifier, date) VALUES (1, ?, '2024-01-01')",
        (xp_modifier,),
    )
    cur.execute(
        "CREATE TABLE lifestyle (user_id INTEGER, sleep_hours REAL, stress REAL, training_discipline REAL, mental_health REAL, nutrition REAL, fitness REAL)"
    )
    cur.execute(
        "INSERT INTO lifestyle (user_id, sleep_hours, stress, training_discipline, mental_health, nutrition, fitness) VALUES (1, ?, ?, ?, ?, ?, ?)",
        lifestyle,
    )
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, learning_style TEXT)")
    cur.execute("INSERT INTO users (id, learning_style) VALUES (1, ?)", (learning_style,))
    conn.commit()
    conn.close()
    return db


def test_skill_gain_with_modifiers(tmp_path: Path) -> None:
    db = _setup_db(tmp_path, xp_modifier=1.5)
    svc = SkillService(xp_events=DummyXPEvents(2.0), db_path=db)
    skill = Skill(id=1, name="guitar", category="instrument")

    updated = svc.train(1, skill, 10)
    assert updated.xp == 30
    assert updated.level == 1

    updated = svc.train(1, skill, 40)
    assert updated.xp == 150
    assert updated.level == 2


def test_new_player_multiplier(monkeypatch: pytest.MonkeyPatch) -> None:
    old_cfg = get_config()
    set_config(XPConfig(new_player_multiplier=2.0))
    svc = SkillService(xp_events=DummyXPEvents(1.0))
    monkeypatch.setattr(svc, "_lifestyle_modifier", lambda _uid: 1.0)
    skill = Skill(id=500, name="guitar", category="instrument")
    updated = svc.train(1, skill, 10)
    assert updated.xp == 20
    set_config(old_cfg)


def test_rested_xp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    old_cfg = get_config()
    set_config(XPConfig(rested_xp_rate=2.0))
    db = tmp_path / "db.sqlite"
    svc = SkillService(xp_events=DummyXPEvents(1.0), db_path=db)
    monkeypatch.setattr(svc, "_lifestyle_modifier", lambda _uid: 1.0)
    skill = Skill(id=501, name="guitar", category="instrument")
    base = 1_000.0
    monkeypatch.setattr("backend.services.skill_service.time.time", lambda: base)
    svc.train(1, skill, 10, duration=1)
    # Advance 5 hours to accrue rest
    monkeypatch.setattr(
        "backend.services.skill_service.time.time", lambda: base + 5 * 3600
    )
    updated = svc.train(1, skill, 10, duration=1)
    assert updated.xp == 30  # first 10 + rested bonus 20
    state = svc._rest_state.get(1)
    assert state and state["rest_hours"] == pytest.approx(4.0, rel=1e-3)
    set_config(old_cfg)


def test_max_multiplier_caps_xp(monkeypatch: pytest.MonkeyPatch) -> None:
    old_cfg = get_config()
    set_config(XPConfig(max_multiplier=2.0))
    svc = SkillService(xp_events=DummyXPEvents(10.0))
    monkeypatch.setattr(
        "backend.services.skill_service.xp_item_service.get_active_multiplier",
        lambda _uid: 5.0,
    )
    monkeypatch.setattr(svc, "_lifestyle_modifier", lambda _uid: 1.0)
    skill = Skill(id=50, name="guitar", category="instrument")
    updated = svc.train(1, skill, 10)
    assert updated.xp == 20
    set_config(old_cfg)


def test_skill_daily_cap() -> None:
    old_cfg = get_config()
    set_config(XPConfig(daily_cap=100))
    svc = SkillService(xp_events=DummyXPEvents(1.0))
    skill = Skill(id=2, name="drums", category="instrument")

    svc.train(1, skill, 80)
    updated = svc.train(1, skill, 50)

    assert updated.xp == 100
    assert updated.level == 2
    set_config(old_cfg)


def test_skill_level_cap() -> None:
    old_cfg = get_config()
    set_config(XPConfig(level_cap=5))
    svc = SkillService(xp_events=DummyXPEvents(1.0))
    skill = Skill(id=25, name="piano", category="instrument")

    updated = svc.train(1, skill, 600)
    assert updated.level == 5

    updated = svc.train(1, skill, 400)
    assert updated.level == 5
    set_config(old_cfg)


def test_level_cap_clamps_only_level() -> None:
    old_cfg = get_config()
    set_config(XPConfig(level_cap=3))
    svc = SkillService(xp_events=DummyXPEvents(1.0))
    skill = Skill(id=26, name="violin", category="instrument")

    updated = svc.train(1, skill, 1000)
    assert updated.level == 3
    assert updated.xp == 1000

    updated = svc.train(1, skill, 500)
    assert updated.level == 3
    assert updated.xp == 1500
    set_config(old_cfg)


def test_skill_decay() -> None:
    svc = SkillService(xp_events=DummyXPEvents(1.0))
    skill = Skill(id=3, name="vocals", category="performance")

    svc.train(1, skill, 120)
    updated = svc.apply_decay(1, 3, 30)

    assert updated.xp == 90
    assert updated.level == 1


def test_training_updates_avatar_stats() -> None:
    svc = SkillService(xp_events=DummyXPEvents(1.0), avatar_service=DummyAvatarService())
    skill = Skill(id=99, name="guitar", category="instrument")

    svc.train(1, skill, 10, duration=5)
    svc.train_with_method(1, skill, LearningMethod.PRACTICE, 4)

    updates = svc.avatar_service.updates
    fatigue = [u for _, u in updates if getattr(u, "fatigue", None) is not None]
    stamina = [u for _, u in updates if getattr(u, "stamina", None) is not None]
    assert fatigue and fatigue[0].fatigue == 5
    assert stamina and stamina[-1].stamina == 98


def _setup_device() -> int:
    """Create an internet device item and reset inventory state."""
    import sys
    import types

    if "backend.services.notifications_service" not in sys.modules:
        sys.modules["backend.services.notifications_service"] = types.SimpleNamespace(
            NotificationsService=object
        )
    from backend.services.item_service import item_service as svc

    global item_service
    item_service = svc

    with sqlite3.connect(item_service.db_path) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM user_items")
        cur.execute("DELETE FROM items")
        conn.commit()
    item_service.ensure_schema()
    device = item_service.create_item(
        Item(id=None, name="internet device", category="tech")
    )
    return device.id


def test_youtube_requires_internet_device() -> None:
    svc = SkillService()
    skill = Skill(id=10, name="guitar", category="instrument")
    _setup_device()

    with pytest.raises(ValueError):
        svc.train_with_method(1, skill, LearningMethod.YOUTUBE, 1)


def test_youtube_plateau() -> None:
    svc = SkillService()
    skill = Skill(id=11, name="guitar", category="instrument")
    device_id = _setup_device()
    item_service.add_to_inventory(1, device_id)

    svc.train(1, skill, 1000)

    with pytest.raises(ValueError):
        svc.train_with_method(1, skill, LearningMethod.YOUTUBE, 1)


def test_breakthrough_double_xp(monkeypatch: pytest.MonkeyPatch) -> None:
    svc = SkillService()
    skill = Skill(id=12, name="guitar", category="instrument")
    device_id = _setup_device()
    item_service.add_to_inventory(1, device_id)

    monkeypatch.setattr(
        "backend.services.skill_service.random.random", lambda: 0.01
    )
    updated = svc.train_with_method(1, skill, LearningMethod.YOUTUBE, 1)
    assert updated.xp == 100

    monkeypatch.setattr(
        "backend.services.skill_service.random.random", lambda: 0.99
    )
    updated = svc.train_with_method(1, skill, LearningMethod.YOUTUBE, 1)
    assert updated.xp == 145


def test_learning_style_bonus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = _setup_db(tmp_path, learning_style="visual")
    svc = SkillService(db_path=db)
    skill = Skill(id=20, name="guitar", category="instrument")
    device_id = _setup_device()
    item_service.add_to_inventory(1, device_id)
    monkeypatch.setattr(
        "backend.services.skill_service.random.random", lambda: 0.99
    )
    updated = svc.train_with_method(1, skill, LearningMethod.YOUTUBE, 1)
    assert updated.xp == 60


def test_environment_quality(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = _setup_db(tmp_path)
    svc = SkillService(db_path=db)
    skill = Skill(id=21, name="drums", category="instrument")
    monkeypatch.setattr(
        "backend.services.skill_service.random.random", lambda: 0.99
    )
    updated = svc.train_with_method(
        1, skill, LearningMethod.PRACTICE, 1, environment_quality=1.5
    )
    assert updated.xp == 15


def test_voice_boosts_vocal_xp() -> None:
    class DummyAvatar:
        def __init__(self, voice: int):
            self.voice = voice
            self.discipline = 50
            self.creativity = 50
            self.charisma = 0
            self.intelligence = 50
            self.fatigue = 0

    class DummyAvatarService:
        def __init__(self, avatar: DummyAvatar):
            self.avatar = avatar

        def get_avatar(self, user_id: int) -> DummyAvatar:
            return self.avatar

    svc = SkillService(avatar_service=DummyAvatarService(DummyAvatar(80)))
    skill = Skill(id=SKILL_NAME_TO_ID["vocals"], name="vocals", category="performance")
    updated = svc.train(1, skill, 100)
    assert updated.xp == 140


def test_lifestyle_modifier(tmp_path: Path) -> None:
    db = _setup_db(tmp_path, lifestyle=(4, 90, 50, 100, 100, 100))
    svc = SkillService(db_path=db, xp_events=DummyXPEvents(1.0))
    skill = Skill(id=22, name="bass", category="instrument")
    updated = svc.train(1, skill, 10)
    assert updated.xp == 5


def test_method_burnout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = _setup_db(tmp_path)
    svc = SkillService(db_path=db)
    skill = Skill(id=23, name="piano", category="instrument")
    monkeypatch.setattr(
        "backend.services.skill_service.random.random", lambda: 0.99
    )
    svc.train_with_method(1, skill, LearningMethod.PRACTICE, 1)
    svc.train_with_method(1, skill, LearningMethod.PRACTICE, 1)
    updated = svc.train_with_method(1, skill, LearningMethod.PRACTICE, 1)
    assert updated.xp == 27


def test_burnout_recovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = _setup_db(tmp_path)
    svc = SkillService(db_path=db)
    skill = Skill(id=24, name="piano", category="instrument")
    monkeypatch.setattr(
        "backend.services.skill_service.random.random", lambda: 0.99
    )
    svc.train_with_method(1, skill, LearningMethod.PRACTICE, 1)
    svc.train_with_method(1, skill, LearningMethod.PRACTICE, 1)
    svc.reduce_burnout(1, amount=2)
    updated = svc.train_with_method(1, skill, LearningMethod.PRACTICE, 1)
    assert updated.xp == 29


def test_synergy_bonus_applied() -> None:
    svc = SkillService()
    spec = SkillSpecialization(name="lead", related_skills={31: 2}, bonus=0.5)
    guitar = Skill(id=30, name="guitar", category="instrument", specializations={"lead": spec})
    theory = Skill(id=31, name="music theory", category="knowledge")
    svc.select_specialization(1, guitar, "lead")
    svc.train(1, theory, 200)
    updated = svc.train(1, guitar, 100)
    assert updated.xp == 150


def test_prerequisite_requirements() -> None:
    svc = SkillService()
    keyboard = Skill(id=40, name="keyboard", category="instrument")
    piano = Skill(
        id=41,
        name="piano",
        category="instrument",
        parent_id=40,
        prerequisites={40: 100},
    )

    with pytest.raises(ValueError):
        svc.train_with_method(1, piano, LearningMethod.PRACTICE, 1)

    svc.train(1, keyboard, 9900)
    updated = svc.train_with_method(1, piano, LearningMethod.PRACTICE, 1)
    assert updated.xp > 0



VOCAL_SUBSKILLS = [
    "breath_control",
    "vibrato_control",
    "harmonization",
    "falsetto",
    "screaming",
]


@pytest.mark.parametrize("skill_name", VOCAL_SUBSKILLS)
def test_vocal_prerequisites_and_leveling(
    skill_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    svc = SkillService(xp_events=DummyXPEvents(1.0))
    training = VocalTrainingService(svc)
    monkeypatch.setattr(
        "backend.services.skill_service.random.random", lambda: 0.99
    )

    # prerequisites not met
    with pytest.raises(ValueError):
        training.practice(1, skill_name, 1)

    vocals = Skill(id=SKILL_NAME_TO_ID["vocals"], name="vocals", category="performance")
    svc.train(1, vocals, 9900)

    result = training.practice(1, skill_name, 10)
    assert result.xp == 100
    assert result.level == 2

@pytest.mark.parametrize(
    "skill_name",
    [
        "audio_engineering",
        "multitrack_recording",
        "microphone_technique",
        "audio_editing",
        "sound_design",
        "beat_programming",
        "midi_programming",
        "vocal_tuning",
        "sample_management",
        "studio_acoustics",
    ],
)
def test_music_production_subskills_persist(
    skill_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "backend.services.skill_service.random.random", lambda: 0.99
    )
    svc = RecordingService()
    user_id = 100 + SKILL_NAME_TO_ID[skill_name]

    updated = svc.practice_skill(user_id, skill_name, 10)
    assert updated.xp == 100
    assert updated.level == 2

    refreshed = svc.practice_skill(user_id, skill_name, 0)
    assert refreshed.xp == 100
    assert refreshed.level == 2

