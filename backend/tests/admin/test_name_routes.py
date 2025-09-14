import asyncio
import importlib
import types
import fastapi
from fastapi import Request

from services import name_dataset_service
from backend.utils import name_generator


def test_append_names_and_generate(tmp_path, monkeypatch):
    class DummyRouter:
        def __init__(self, *args, **kwargs):
            pass
        def post(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    monkeypatch.setattr(fastapi, "APIRouter", DummyRouter)

    admin_name_routes = importlib.import_module("backend.routes.admin_name_routes")

    monkeypatch.setattr(name_dataset_service, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(name_generator, "DATA_DIR", tmp_path)

    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(admin_name_routes, "get_current_user_id", fake_current_user)
    monkeypatch.setattr(admin_name_routes, "require_permission", fake_require_permission)

    req = Request({"type": "http"})
    asyncio.run(admin_name_routes.add_first_name(admin_name_routes.FirstNameIn(name="Testo", gender="male"), req))
    asyncio.run(admin_name_routes.add_surname(admin_name_routes.SurnameIn(name="Testson"), req))

    name_generator.MALE_FIRST_NAMES = name_generator._load_names("male_names.csv")
    name_generator.LAST_NAMES = name_generator._load_names("surnames.csv")

    monkeypatch.setattr(name_generator.random, "choice", lambda seq: seq[-1])
    result = name_generator.generate_random_name(gender="male")
    assert result == "Testo Testson"
