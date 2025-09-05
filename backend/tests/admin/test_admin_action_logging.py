import asyncio
import json
import os
import tempfile

from fastapi import Request

from backend.routes import admin_media_moderation_routes as media_routes
from backend.services.admin_service import AdminService, AdminActionRepository
from backend.storage.local import LocalStorage
from backend.services import storage_service
from backend.utils.db import get_conn


def _setup(monkeypatch):
    """Prepare isolated storage and database for tests."""

    async def fake_current_user(req: Request):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(media_routes, "get_current_user_id", fake_current_user)
    monkeypatch.setattr(media_routes, "require_permission", fake_require_permission)

    # fresh storage backend in a temp directory
    tmpdir = tempfile.TemporaryDirectory()
    storage = LocalStorage(tmpdir.name)
    storage_service._backend = None  # reset global cache
    monkeypatch.setattr(media_routes, "get_storage_backend", lambda: storage)

    # temporary sqlite database
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    monkeypatch.setattr(
        media_routes,
        "admin_logger",
        AdminService(AdminActionRepository(db_path)),
    )

    return storage, db_path, tmpdir


def test_flag_media_logs_action_and_stores(monkeypatch):
    storage, db_path, tmpdir = _setup(monkeypatch)
    req = Request({"type": "http"})

    asyncio.run(media_routes.flag_media(5, req))

    with get_conn(db_path) as conn:
        row = conn.execute("SELECT * FROM admin_actions").fetchone()

    assert row["action_type"] == "media_flag"
    key = f"admin-actions/{row['id']}.json"
    assert storage.exists(key)

    with open(os.path.join(tmpdir.name, key)) as f:
        data = json.load(f)
    assert data["payload"]["media_id"] == 5


def test_approve_media_logs_action_and_stores(monkeypatch):
    storage, db_path, tmpdir = _setup(monkeypatch)
    req = Request({"type": "http"})

    asyncio.run(media_routes.approve_media(7, req))

    with get_conn(db_path) as conn:
        row = conn.execute("SELECT * FROM admin_actions").fetchone()

    assert row["action_type"] == "media_approve"
    key = f"admin-actions/{row['id']}.json"
    assert storage.exists(key)

    with open(os.path.join(tmpdir.name, key)) as f:
        data = json.load(f)
    assert data["payload"]["media_id"] == 7

