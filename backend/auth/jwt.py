# File: backend/auth/jwt.py
import os, time, json, hmac, base64, hashlib
from typing import Dict, Any, Optional

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _b64url_json(obj: Dict[str, Any]) -> str:
    return _b64url(json.dumps(obj, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))

def _b64url_decode(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def _sign(msg: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).digest()
    return _b64url(sig)

def encode(payload: Dict[str, Any], secret: str, header: Optional[Dict[str, Any]] = None) -> str:
    header = header or {'alg': 'HS256', 'typ': 'JWT'}
    h = _b64url_json(header)
    p = _b64url_json(payload)
    msg = f"{h}.{p}".encode('utf-8')
    s = _sign(msg, secret)
    return f"{h}.{p}.{s}"

def decode(token: str, secret: str, verify_exp: bool = True, leeway: int = 0, expected_iss: Optional[str] = None, expected_aud: Optional[str] = None) -> Dict[str, Any]:
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError('invalid token')
    h_b64, p_b64, s_b64 = parts
    msg = f"{h_b64}.{p_b64}".encode('utf-8')
    expected_sig = _sign(msg, secret)
    if not hmac.compare_digest(expected_sig, s_b64):
        raise ValueError('invalid signature')
    payload = json.loads(_b64url_decode(p_b64).decode('utf-8'))
    now = int(time.time())
    if verify_exp and 'exp' in payload and now > int(payload['exp']) + int(leeway):
        raise ValueError('token expired')
    if expected_iss and payload.get('iss') != expected_iss:
        raise ValueError('issuer mismatch')
    if expected_aud and payload.get('aud') != expected_aud:
        raise ValueError('audience mismatch')
    return payload

def now_ts() -> int:
    import time
    return int(time.time())
