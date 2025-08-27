from datetime import datetime, timedelta

from core.config import settings
from jose import jwt
from services.auth_service import get_user_by_username, verify_password


def create_access_token(username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN)
    to_encode = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def verify_user_credentials(username: str, password: str) -> dict:
    user = get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        return {"username": user["username"], "role": user["role"]}
    return None
