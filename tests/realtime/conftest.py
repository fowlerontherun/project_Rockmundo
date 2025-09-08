import importlib
import pathlib
import sys
import types

import pytest
from fastapi import FastAPI

# Ensure project root on sys.path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

from tests.realtime.fake_jam_service import FakeJamService


@pytest.fixture
def jam_app():
    fake_module = types.ModuleType("jam_service")
    fake_module.JamService = FakeJamService
    original_mod = sys.modules.get("backend.services.jam_service")
    sys.modules["backend.services.jam_service"] = fake_module

    jam_gateway = importlib.reload(importlib.import_module("backend.realtime.jam_gateway"))

    app = FastAPI()
    service = FakeJamService()
    jam_gateway.jam_service = service
    app.include_router(jam_gateway.router)

    async def _uid() -> int:
        return 1

    app.dependency_overrides[jam_gateway.get_current_user_id_dep] = _uid
    try:
        yield app, service
    finally:
        if original_mod is not None:
            sys.modules["backend.services.jam_service"] = original_mod
        else:
            sys.modules.pop("backend.services.jam_service", None)
        importlib.reload(jam_gateway)
