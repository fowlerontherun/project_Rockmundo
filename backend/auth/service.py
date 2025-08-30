# File: backend/auth/service.py
from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import hashlib, secrets, uuid

from utils.db import get_conn
from core.security import hash_password, verify_password
from auth import jwt as jwt_helper
from core.config import settings

UTC = timezone.utc

def _now() -> datetime:
    from datetime import datetime
    return datetime.now(UTC)

def _ts(dt: datetime) -> int:
    return int(dt.timestamp())

class AuthService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    # --- users ---
    def register(self, email: str, password: str, display_name: str = "") -> Dict[str, Any]:
        email = email.strip().lower()
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email=?", (email,))
            if cur.fetchone():
                raise ValueError("EMAIL_TAKEN")
            pw = hash_password(password)
            cur.execute("INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)", (email, pw, display_name))
            user_id = int(cur.lastrowid)
            # default role 'user'
            cur.execute("INSERT OR IGNORE INTO roles(name) VALUES('user')")
            cur.execute("INSERT INTO user_roles (user_id, role_id) SELECT ?, id FROM roles WHERE name='user'", (user_id,))
            cur.execute("INSERT INTO audit_log (user_id, action, meta) VALUES (?, 'user.register', json_object('email', ?))", (user_id, email))
            return {"id": user_id, "email": email, "display_name": display_name}

    # --- tokens ---
    def _make_access_token(self, user_id: int) -> str:
        """Create an access JWT for a user and persist its identifier.

        A unique ``jti`` (JWT ID) is added to the payload and stored in the
        ``access_tokens`` table so that the token can later be revoked.
        """

        now = jwt_helper.now_ts()
        exp = now + settings.auth.access_token_ttl_min * 60
        jti = uuid.uuid4().hex
        payload = {
            "iss": settings.auth.jwt_iss,
            "aud": settings.auth.jwt_aud,
            "iat": now,
            "nbf": now,
            "exp": exp,
            "sub": str(user_id),
            "jti": jti,
        }
        token = jwt_helper.encode(payload, secret=settings.auth.jwt_secret)
        expires_at = datetime.fromtimestamp(exp, UTC).isoformat()
        with get_conn(self.db_path) as conn:
            conn.execute(
                "INSERT INTO access_tokens (jti, user_id, expires_at) VALUES (?, ?, ?)",
                (jti, user_id, expires_at),
            )
        return token

    def _hash_refresh(self, token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def _new_refresh_token(self, user_id: int, user_agent: str = "", ip: str = "") -> Dict[str, Any]:
        token = secrets.token_urlsafe(48)
        token_hash = self._hash_refresh(token)
        expires = _now() + timedelta(days=settings.auth.refresh_token_ttl_days)
        with get_conn(self.db_path) as conn:
            conn.execute("""INSERT INTO refresh_tokens (user_id, token_hash, expires_at, user_agent, ip)
                          VALUES (?, ?, ?, ?, ?)""", (user_id, token_hash, expires.isoformat(), user_agent[:200], ip[:64]))
        return {"refresh_token": token, "expires_at": expires.isoformat()}

    def login(self, email: str, password: str, user_agent: str = "", ip: str = "") -> Dict[str, Any]:
        email = email.strip().lower()
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, password_hash, is_active FROM users WHERE email=?", (email,))
            row = cur.fetchone()
            if not row or row[2] == 0 or not verify_password(password, row[1]):
                raise ValueError("INVALID_CREDENTIALS")
            user_id = int(row[0])
            access = self._make_access_token(user_id)
            refresh = self._new_refresh_token(user_id, user_agent=user_agent, ip=ip)
            conn.execute("INSERT INTO audit_log (user_id, action, meta) VALUES (?, 'auth.login', json_object('ua', ?, 'ip', ?))", (user_id, user_agent, ip))
            return {"access_token": access, **refresh, "token_type": "Bearer"}

    def refresh(self, refresh_token: str, user_agent: str = "", ip: str = "") -> Dict[str, Any]:
        token_hash = self._hash_refresh(refresh_token)
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""SELECT user_id, expires_at, revoked_at FROM refresh_tokens
                           WHERE token_hash=?""", (token_hash,))
            row = cur.fetchone()
            if not row:
                raise ValueError("REFRESH_INVALID")
            user_id = int(row[0])
            if row[2] is not None:
                raise ValueError("REFRESH_REVOKED")
            if row[1] < _now().isoformat():
                raise ValueError("REFRESH_EXPIRED")
            # rotate: revoke old, issue new
            conn.execute("UPDATE refresh_tokens SET revoked_at=datetime('now') WHERE token_hash=?", (token_hash,))
            access = self._make_access_token(user_id)
            new_r = self._new_refresh_token(user_id, user_agent=user_agent, ip=ip)
            conn.execute("INSERT INTO audit_log (user_id, action, meta) VALUES (?, 'auth.refresh', json_object('ua', ?, 'ip', ?))", (user_id, user_agent, ip))
            return {"access_token": access, **new_r, "token_type": "Bearer"}

    def logout(self, refresh_token: str) -> Dict[str, Any]:
        token_hash = self._hash_refresh(refresh_token)
        with get_conn(self.db_path) as conn:
            conn.execute("UPDATE refresh_tokens SET revoked_at=datetime('now') WHERE token_hash=?", (token_hash,))
        return {"ok": True}

    # --- access token management ---
    def revoke_access_token(self, jti: str) -> bool:
        """Revoke an access token by its JWT ID."""
        with get_conn(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE access_tokens SET revoked_at=datetime('now') WHERE jti=? AND revoked_at IS NULL",
                (jti,),
            )
            return cur.rowcount > 0
