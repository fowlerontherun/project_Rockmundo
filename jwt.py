import base64
import hashlib
import hmac
import json
from typing import Any, Dict, List, Optional

DEFAULT_ALG = "HS256"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def encode(payload: Dict[str, Any], secret: str, algorithm: str = DEFAULT_ALG) -> str:
    header = {"alg": algorithm, "typ": "JWT"}
    segments = [_b64(json.dumps(header).encode()), _b64(json.dumps(payload).encode())]
    signing_input = ".".join(segments).encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    segments.append(_b64(sig))
    return ".".join(segments)


def decode(
    token: str,
    secret: str,
    algorithms: Optional[List[str]] = None,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    leeway: int = 0,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    header_b64, payload_b64, signature_b64 = token.split(".")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if _b64(sig) != signature_b64:
        raise ValueError("Invalid signature")
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
    return payload
