from backend.models.npc import NPC
import services.npc_ai_service as npc_ai_module
from backend.services.npc_ai_service import npc_ai_service
from backend.services import event_service
from backend.services.npc_service import NPCService


def test_generate_daily_behavior(monkeypatch):
    npc = NPC(
        id=1,
        identity="TestNPC",
        npc_type="artist",
        goals={"gig": True, "release": True},
        routine={"preferred_venue": "Town Hall"},
        interaction_hooks={"hello": "Hi there!"},
    )
    monkeypatch.setattr(npc_ai_module.random, "random", lambda: 0.0)
    events = npc_ai_service.generate_daily_behavior(npc)
    types = {e["type"] for e in events}
    assert {"gig", "release", "interaction"} <= types


def test_npc_persistence_with_new_fields():
    svc = NPCService()
    npc = svc.create_npc(
        "NPC",
        "merchant",
        goals={"gig": True},
        routine={"schedule": "daily"},
        interaction_hooks={"greet": "hello"},
    )
    stored = svc.get_npc(npc["id"])
    assert stored["goals"]["gig"]
    assert stored["routine"]["schedule"] == "daily"
    assert stored["interaction_hooks"]["greet"] == "hello"


def test_roll_for_npc_daily_events(monkeypatch):
    npc = NPC(
        id=2,
        identity="NPC2",
        npc_type="artist",
        goals={"gig": True},
        routine={},
        interaction_hooks={}
    )
    monkeypatch.setattr(npc_ai_module.random, "random", lambda: 0.0)
    events = event_service.roll_for_npc_daily_events(npc)
    assert events and events[0]["type"] == "gig"
