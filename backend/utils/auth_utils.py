from datetime import datetime, timedelta

codex/consolidate-jwt-library-usage
from auth.jwt import encode
from core.config import settings
from services.auth_service import get_user_by_username, verify_password


ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_TTL_MIN


def create_access_token(username: str, role: str) -> str:
    """Create a signed JWT for the given user."""

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": username,
        "role": role,
        "exp": expire,
        "iss": settings.JWT_ISS,
        "aud": settings.JWT_AUD,
    }
    return encode(to_encode, settings.JWT_SECRET)


def verify_user_credentials(username: str, password: str) -> dict | None:
    """Validate a username/password pair and return basic user info."""
=======
from core.config import settings
from jose import jwt
from services.auth_service import get_user_by_username, verify_password


def create_access_token(username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN)
    to_encode = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
main

    user = get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        return {"username": user["username"], "role": user["role"]}
    return None
