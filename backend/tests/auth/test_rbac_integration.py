from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import get_current_user_id, require_permission
from backend.auth import rbac


async def require_admin_dep(user_id: int = Depends(get_current_user_id)):
    return await require_permission(["admin"], user_id)


async def require_user_dep(user_id: int = Depends(get_current_user_id)):
    return await require_permission(["user"], user_id)


router_a = APIRouter()
router_b = APIRouter()


@router_a.get("/metrics", dependencies=[Depends(require_admin_dep)])
def metrics() -> dict:
    return {"ok": True}


@router_b.get("/shop", dependencies=[Depends(require_user_dep)])
def shop() -> dict:
    return {"ok": True}


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router_a)
    app.include_router(router_b)
    app.dependency_overrides[get_current_user_id] = lambda: 1
    return app


def test_permission_enforcement_across_modules(monkeypatch):
    app = create_app()
    client = TestClient(app)

    allowed = {"admin"}

    def fake_has_permission(uid: int, perm: str) -> bool:
        return perm in allowed

    monkeypatch.setattr(rbac.rbac_service, "has_permission", fake_has_permission)

    assert client.get("/metrics").status_code == 200
    assert client.get("/shop").status_code == 403

    allowed.add("user")
    assert client.get("/shop").status_code == 200
