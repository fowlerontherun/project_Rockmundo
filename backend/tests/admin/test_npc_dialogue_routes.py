import asyncio

import asyncio

import pytest
from fastapi import HTTPException, Request

from routes.admin_npc_routes import create_npc
from routes.admin_npc_dialogue_routes import edit_dialogue, preview_dialogue, svc


def _allow_admin(monkeypatch):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "routes.admin_npc_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "routes.admin_npc_routes.require_permission", fake_require_permission
    )
    monkeypatch.setattr(
        "routes.admin_npc_dialogue_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "routes.admin_npc_dialogue_routes.require_permission", fake_require_permission
    )


def test_dialogue_routes_require_admin():
    req = Request({})
    with pytest.raises(HTTPException):
        asyncio.run(edit_dialogue(1, {}, req))
    with pytest.raises(HTTPException):
        asyncio.run(preview_dialogue(1, {"choices": []}, req))


def test_edit_and_preview_dialogue(monkeypatch):
    _allow_admin(monkeypatch)
    req = Request({})
    npc = asyncio.run(create_npc({"identity": "T", "npc_type": "type"}, req))
    npc_id = npc["id"]
    tree = {
        "root": "start",
        "nodes": {
            "start": {
                "id": "start",
                "text": "hi",
                "responses": [
                    {"text": "bye", "next_id": None}
                ],
            }
        },
    }
    saved = asyncio.run(edit_dialogue(npc_id, tree, req))
    assert saved["root"] == "start"
    preview = asyncio.run(preview_dialogue(npc_id, {"choices": [0]}, req))
    assert preview == {"lines": ["hi", "bye"]}
    # ensure service data is stored
    assert svc.get_npc(npc_id)["dialogue_hooks"]["root"] == "start"
