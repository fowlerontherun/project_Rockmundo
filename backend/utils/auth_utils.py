from datetime import datetime, timedelta
from jose import jwt
from services.auth_service import get_user_by_username, verify_password

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_user_credentials(username: str, password: str) -> dict:
    user = get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        return {"username": user["username"], "role": user["role"]}
    return None