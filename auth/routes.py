# File: backend/auth/routes.py
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

from .dependencies import get_current_user_id, require_admin
from .permissions import Permissions
from .service import AuthService
from fastapi import APIRouter, Depends, HTTPException, Request
from models.admin import AdminSession, admin_sessions
from utils.db import aget_conn

from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/auth", tags=["Auth"])
svc = AuthService()

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = ""

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class RefreshIn(BaseModel):
    refresh_token: str = Field(..., min_length=20)

class LogoutIn(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class RevokeTokenIn(BaseModel):
    jti: str


@router.get("/permissions")
async def list_permissions():
    """Return the list of available permission strings."""
    return {"permissions": [p.value for p in Permissions]}

@router.post("/register")
async def register(payload: RegisterIn):
    try:
        return await svc.register(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name or "",
        )
    except ValueError as e:
        code = str(e)
        if code == "EMAIL_TAKEN":
            raise HTTPException(
                status_code=409,
                detail={"code": "EMAIL_TAKEN", "message": "Email already registered"},
            )
        raise

@router.post("/login")
async def login(req: Request, payload: LoginIn):
    ua = req.headers.get("user-agent", "")
    ip = req.client.host if req.client else ""
    try:
        return await svc.login(
            email=payload.email,
            password=payload.password,
            user_agent=ua,
            ip=ip,
        )
    except ValueError as e:
        if str(e) == "INVALID_CREDENTIALS":
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password",
                },
            )
        raise

@router.post("/refresh")
async def refresh(req: Request, payload: RefreshIn):
    ua = req.headers.get("user-agent", "")
    ip = req.client.host if req.client else ""
    try:
        return await svc.refresh(
            refresh_token=payload.refresh_token, user_agent=ua, ip=ip
        )
    except ValueError as e:
        code = str(e)
        mapping = {
            "REFRESH_INVALID": (401, "Refresh token invalid"),
            "REFRESH_REVOKED": (401, "Refresh token revoked"),
            "REFRESH_EXPIRED": (401, "Refresh token expired"),
        }
        status_code, msg = mapping.get(code, (400, code))
        raise HTTPException(status_code=status_code, detail={"code": code, "message": msg})

@router.post("/logout")
async def logout(payload: LogoutIn):
    return await svc.logout(refresh_token=payload.refresh_token)


@router.post(
    "/tokens/revoke",
    dependencies=[Depends(require_admin)],
)
async def revoke_token(payload: RevokeTokenIn):
    if not await svc.revoke_access_token(payload.jti):
        raise HTTPException(
            status_code=404,
            detail={"code": "TOKEN_NOT_FOUND", "message": "Token not found"},
        )
    return {"ok": True}

@router.get("/me")
async def me(user_id: int = Depends(get_current_user_id)):
    async with aget_conn() as conn:
        cur = await conn.execute(
            "SELECT id, email, display_name, is_active, created_at FROM users WHERE id=?",
            (user_id,),
        )
        row = await cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail={"code": "USER_NOT_FOUND", "message": "User not found"},
            )
        roles_cur = await conn.execute(
            '''SELECT r.name FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE ur.user_id=?''',
            (user_id,),
        )
        roles = await roles_cur.fetchall()
        return {**dict(row), "roles": [r["name"] for r in roles]}

# Admin role management
class RoleAssignIn(BaseModel):
    user_id: int
    role: str

@router.post(
    "/roles/assign",
    dependencies=[Depends(require_admin)],
)
async def assign_role(payload: RoleAssignIn):
    async with aget_conn() as conn:
        cur = await conn.execute("SELECT id FROM roles WHERE name=?", (payload.role,))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(
                status_code=404,
                detail={"code": "ROLE_NOT_FOUND", "message": "Role not found"},
            )
        await conn.execute(
            "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
            (payload.user_id, r["id"]),
        )
        return {"ok": True}

@router.post(
    "/roles/revoke",
    dependencies=[Depends(require_admin)],
)
async def revoke_role(payload: RoleAssignIn):
    async with aget_conn() as conn:
        cur = await conn.execute("SELECT id FROM roles WHERE name=?", (payload.role,))
        r = await cur.fetchone()
        if not r:
            raise HTTPException(
                status_code=404,
                detail={"code": "ROLE_NOT_FOUND", "message": "Role not found"},
            )
        await conn.execute(
            "DELETE FROM user_roles WHERE user_id=? AND role_id=?",
            (payload.user_id, r["id"]),
        )
        return {"ok": True}


# --- Admin MFA endpoints ----------------------------------------------------

admin_mfa_router = APIRouter(prefix="/admin/mfa", tags=["AdminMFA"])


class MFASetupIn(BaseModel):
    device: str


class MFAVerifyIn(BaseModel):
    session_id: str
    code: str


@admin_mfa_router.post("/setup")
def mfa_setup(request: Request, payload: MFASetupIn):
    code = f"{random.randint(0, 999999):06d}"
    session_id = uuid.uuid4().hex
    ip = request.client.host if request.client else ""
    session = AdminSession(
        id=session_id,
        device=payload.device,
        ip=ip,
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    admin_sessions[session_id] = session
    # In a real app the code would be delivered via an out-of-band channel; we
    # return it directly here to simplify testing.
    return {"session_id": session_id, "code": code}


@admin_mfa_router.post("/verify")
def mfa_verify(payload: MFAVerifyIn):
    session = admin_sessions.get(payload.session_id)
    if not session or session.is_expired() or session.code != payload.code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    session.verified = True
    return {"ok": True}
