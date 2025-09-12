import asyncio
import fastapi
import pydantic
import pytest

# Provide stubs for missing pydantic features
if not hasattr(pydantic, "EmailStr"):
    pydantic.EmailStr = str  # type: ignore[attr-defined]

    def _field(default, **_kwargs):  # type: ignore[override]
        return default

    pydantic.Field = _field  # type: ignore[attr-defined]


# Allow APIRouter.post to accept **kwargs as used in auth.routes

def _post(self, path: str, **_kwargs):  # type: ignore[override]
    def decorator(func):
        self.routes.append(("POST", path, func))
        return func

    return decorator


fastapi.APIRouter.post = _post  # type: ignore[attr-defined]

from backend.auth.routes import mfa_setup, mfa_verify, MFASetupIn, MFAVerifyIn
from middleware.admin_mfa import AdminMFAMiddleware


class DummyClient:
    def __init__(self, host: str):
        self.host = host


class DummyRequest:
    def __init__(self, path: str, headers: dict | None = None, host: str = "test"):
        self.path = path
        self.headers = headers or {}
        self.client = DummyClient(host)


async def _ok(_req):
    return "ok"


def test_mfa_setup_and_verify():
    # Setup MFA session
    req = DummyRequest(path="/admin/mfa/setup", host="1.2.3.4")
    data = mfa_setup(req, MFASetupIn(device="tester"))
    session_id, code = data["session_id"], data["code"]

    # Middleware should block access prior to verification
    mw = AdminMFAMiddleware()
    admin_req = DummyRequest(path="/admin/ping")
    with pytest.raises(PermissionError):
        asyncio.run(mw.dispatch(admin_req, _ok))

    # Verify code
    mfa_verify(MFAVerifyIn(session_id=session_id, code=code))

    # Access with valid session id should pass
    admin_req.headers["X-Admin-Session"] = session_id
    assert asyncio.run(mw.dispatch(admin_req, _ok)) == "ok"
