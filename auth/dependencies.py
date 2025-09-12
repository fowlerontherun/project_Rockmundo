# File: backend/auth/dependencies.py
from typing import Iterable, List, Optional, Callable

from . import jwt as jwt_helper
from .permissions import Permissions
from core.config import settings
from fastapi import Depends, HTTPException, Request, status
from .rbac import rbac_service
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

async def _check_permissions(user_id: int, permissions: Iterable[Permissions | str]):
    validated: List[str] = []
    for p in permissions:
        try:
            validated.append(Permissions(p).value)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'UNKNOWN_PERMISSION',
                    'message': f'Unknown permission: {p}',
                },
            )
    if any(rbac_service.has_permission(user_id, p) for p in validated):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={'code': 'FORBIDDEN', 'message': 'Insufficient permission'},
    )

def require_permission(
    permissions: Iterable[Permissions | str],
) -> Callable:
    async def _dependency(user_id: int = Depends(get_current_user_id)):
        await _check_permissions(user_id, permissions)
    return _dependency

async def require_role(roles: List[str], user_id: int = Depends(get_current_user_id)) -> bool:
    await _check_permissions(user_id, roles)
    return True

async def require_admin(user_id: int = Depends(get_current_user_id)) -> int:
    await _check_permissions(user_id, [Permissions.ADMIN])
    return user_id
