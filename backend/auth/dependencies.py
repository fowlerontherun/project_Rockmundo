# File: backend/auth/dependencies.py
from typing import List, Optional
from fastapi import Depends, HTTPException, status, Request
from utils.db import get_conn
from auth import jwt as jwt_helper
from core.config import settings

def _extract_bearer_token(req: Request) -> Optional[str]:
    auth = req.headers.get('Authorization') or req.headers.get('authorization')
    if not auth or not auth.lower().startswith('bearer '):
        return None
    return auth.split(' ', 1)[1].strip()

async def get_current_user_id(req: Request) -> int:
    token = _extract_bearer_token(req)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code':'AUTH_REQUIRED','message':'Missing bearer token'})
    try:
        payload = jwt_helper.decode(
            token,
            secret=settings.JWT_SECRET,
            expected_iss=settings.JWT_ISS,
            expected_aud=settings.JWT_AUD,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={'code':'AUTH_INVALID','message':str(e)})
    user_id = int(payload.get('sub', 0))
    jti = payload.get('jti')
    if user_id <= 0 or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'code':'AUTH_INVALID','message':'Invalid token'},
        )

    with get_conn() as conn:
        row = conn.execute(
            "SELECT revoked_at FROM access_tokens WHERE jti=?",
            (jti,),
        ).fetchone()
    if not row or row['revoked_at'] is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'code':'AUTH_REVOKED','message':'Token revoked'},
        )
    return user_id

async def require_role(roles: List[str], user_id: int = Depends(get_current_user_id)) -> bool:
    # allow if any role matches
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT r.name FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = ?
        """, (user_id,)).fetchall()
        user_roles = {r['name'] for r in rows}
    if any(r in user_roles for r in roles):
        return True
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'code':'FORBIDDEN','message':'Insufficient role'})
