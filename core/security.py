# File: backend/core/security.py
import os, hashlib, hmac, base64
from typing import Tuple

PBKDF2_ITERATIONS = 150000

def _b64(x: bytes) -> str:
    return base64.b64encode(x).decode()

def _ub64(x: str) -> bytes:
    return base64.b64decode(x.encode())

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS, dklen=32)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64(salt)}${_b64(dk)}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iter_s, salt_b64, hash_b64 = encoded.split('$')
        assert algo == 'pbkdf2_sha256'
        iterations = int(iter_s)
        salt = _ub64(salt_b64)
        expected = _ub64(hash_b64)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False
