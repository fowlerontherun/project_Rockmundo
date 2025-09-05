# File: backend/auth/dependencies.py
from typing import List, Optional

from auth import jwt as jwt_helper
from core.config import settings
from fastapi import Depends, HTTPException, Request, status
from services.rbac_service import has_permission
from utils.db import aget_conn


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
            secret=settings.auth.jwt_secret,
            expected_iss=settings.auth.jwt_iss,
            expected_aud=settings.auth.jwt_aud,
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

    async with aget_conn() as conn:
        cur = await conn.execute(
            "SELECT revoked_at FROM access_tokens WHERE jti=?",
            (jti,),
        )
        row = await cur.fetchone()
    if not row or row["revoked_at"] is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'code':'AUTH_REVOKED','message':'Token revoked'},
        )
    return user_id


async def require_permission(
    permissions: List[str], user_id: int = Depends(get_current_user_id)
) -> bool:
    """Ensure ``user_id`` has at least one of the required permissions."""
    if any(has_permission(user_id, p) for p in permissions):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={'code': 'FORBIDDEN', 'message': 'Insufficient permission'},
    )


async def require_role(roles: List[str], user_id: int = Depends(get_current_user_id)) -> bool:
    """Backward compatible wrapper around :func:`require_permission`."""
    return await require_permission(roles, user_id)
