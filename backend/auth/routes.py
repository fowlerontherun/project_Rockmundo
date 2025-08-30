# File: backend/auth/routes.py
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import random
import uuid

from auth.service import AuthService
from auth.jwt import decode
from auth.dependencies import get_current_user_id, require_role
from utils.db import get_conn
from models.admin import AdminSession, admin_sessions

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

@router.post("/register")
def register(payload: RegisterIn):
    try:
        return svc.register(email=payload.email, password=payload.password, display_name=payload.display_name or "")
    except ValueError as e:
        code = str(e)
        if code == "EMAIL_TAKEN":
            raise HTTPException(status_code=409, detail={"code":"EMAIL_TAKEN","message":"Email already registered"})
        raise

@router.post("/login")
def login(req: Request, payload: LoginIn):
    ua = req.headers.get('user-agent', '')
    ip = req.client.host if req.client else ''
    try:
        return svc.login(email=payload.email, password=payload.password, user_agent=ua, ip=ip)
    except ValueError as e:
        if str(e) == "INVALID_CREDENTIALS":
            raise HTTPException(status_code=401, detail={"code":"INVALID_CREDENTIALS","message":"Invalid email or password"})
        raise

@router.post("/refresh")
def refresh(req: Request, payload: RefreshIn):
    ua = req.headers.get('user-agent', '')
    ip = req.client.host if req.client else ''
    try:
        return svc.refresh(refresh_token=payload.refresh_token, user_agent=ua, ip=ip)
    except ValueError as e:
        code = str(e)
        mapping = {
            "REFRESH_INVALID": (401, "Refresh token invalid"),
            "REFRESH_REVOKED": (401, "Refresh token revoked"),
            "REFRESH_EXPIRED": (401, "Refresh token expired"),
        }
        status_code, msg = mapping.get(code, (400, code))
        raise HTTPException(status_code=status_code, detail={"code":code, "message":msg})

@router.post("/logout")
def logout(payload: LogoutIn):
    return svc.logout(refresh_token=payload.refresh_token)


@router.post("/tokens/revoke", dependencies=[Depends(require_role(["admin"]))])
def revoke_token(payload: RevokeTokenIn):
    if not svc.revoke_access_token(payload.jti):
        raise HTTPException(status_code=404, detail={"code": "TOKEN_NOT_FOUND", "message": "Token not found"})
    return {"ok": True}

@router.get("/me")
def me(user_id: int = Depends(get_current_user_id)):
    with get_conn() as conn:
        row = conn.execute("SELECT id, email, display_name, is_active, created_at FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"code":"USER_NOT_FOUND","message":"User not found"})
        # roles
        roles = conn.execute("""SELECT r.name FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE ur.user_id=?""", (user_id,)).fetchall()
        return {**dict(row), "roles": [r['name'] for r in roles]}

# Admin role management
class RoleAssignIn(BaseModel):
    user_id: int
    role: str

@router.post("/roles/assign", dependencies=[Depends(require_role(["admin"]))])
def assign_role(payload: RoleAssignIn):
    with get_conn() as conn:
        r = conn.execute("SELECT id FROM roles WHERE name=?", (payload.role,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail={"code":"ROLE_NOT_FOUND","message":"Role not found"})
        conn.execute("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (payload.user_id, r['id']))
        return {"ok": True}

@router.post("/roles/revoke", dependencies=[Depends(require_role(["admin"]))])
def revoke_role(payload: RoleAssignIn):
    with get_conn() as conn:
        r = conn.execute("SELECT id FROM roles WHERE name=?", (payload.role,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail={"code":"ROLE_NOT_FOUND","message":"Role not found"})
        conn.execute("DELETE FROM user_roles WHERE user_id=? AND role_id=?", (payload.user_id, r['id']))
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

