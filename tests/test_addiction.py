
import types, sys, os
from backend.services import addiction_service as global_addiction_service

# Provide a minimal seeds.skill_seed stub required by random_event_service imports
skill_seed = types.SimpleNamespace(SKILL_NAME_TO_ID={})
sys.modules.setdefault("seeds", types.SimpleNamespace(skill_seed=skill_seed))
sys.modules.setdefault("seeds.skill_seed", skill_seed)

# Stub for notifications_service dependency
discord_stub = types.SimpleNamespace(
    DiscordServiceError=Exception, send_message=lambda *args, **kwargs: None
)
sys.modules.setdefault("services", types.SimpleNamespace(discord_service=discord_stub))
sys.modules.setdefault("services.discord_service", discord_stub)
# Minimal utils.db stub
sys.modules.setdefault("utils", types.SimpleNamespace(db=types.SimpleNamespace(get_conn=lambda: None)))
sys.modules.setdefault("utils.db", types.SimpleNamespace(get_conn=lambda: None))

import backend.services.random_event_service as random_event_module
from backend.services.random_event_service import random_event_service


def _service(tmp_path, monkeypatch):
    db_file = tmp_path / "addiction.db"
    svc = global_addiction_service.AddictionService(db_path=str(db_file))
    monkeypatch.setattr(global_addiction_service, "addiction_service", svc)
    return svc


def test_addiction_accumulation(tmp_path, monkeypatch):
    svc = _service(tmp_path, monkeypatch)
    level1 = svc.use(1, "drug", amount=20)
    level2 = svc.use(1, "drug", amount=30)
    assert level1 == 20
    assert level2 == 50


def test_withdrawal_reduces_level(tmp_path, monkeypatch):
    svc = _service(tmp_path, monkeypatch)
    svc.use(1, "drug", amount=40)
    svc.apply_withdrawal(1, decay=10)
    assert svc.get_level(1, "drug") == 30


def test_negative_event_trigger(tmp_path, monkeypatch):
    svc = _service(tmp_path, monkeypatch)
    monkeypatch.setattr(random_event_module, "addiction_service", svc)
    monkeypatch.setattr(random_event_service, "db", None)

    svc.use(1, "drug", amount=80)
    event = random_event_service.trigger_addiction_event(1, date="2024-01-01")
    assert event["type"] == "police_intervention"
