import base64
import hashlib
import hmac
import json
import time
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
    algorithms = algorithms or [DEFAULT_ALG]
    opts = {
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "verify_iss": True,
        "verify_aud": True,
    }
    if options:
        opts.update(options)

    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:  # not enough values to unpack
        raise ValueError("Invalid token") from exc

    header = json.loads(base64.urlsafe_b64decode(header_b64 + "=="))
    alg = header.get("alg", DEFAULT_ALG)
    if alg not in algorithms:
        raise ValueError("Algorithm not allowed")
    if alg != DEFAULT_ALG:
        raise ValueError("Unsupported algorithm")

    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    if _b64(sig) != signature_b64:
        raise ValueError("Invalid signature")

    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))

    now = int(time.time())
    if opts["verify_exp"]:
        exp = payload.get("exp")
        if exp is None:
            raise ValueError("Missing exp claim")
        if now > int(exp) + leeway:
            raise ValueError("Token expired")

    if opts["verify_nbf"] and "nbf" in payload:
        if now < int(payload["nbf"]) - leeway:
            raise ValueError("Token not yet valid")

    if opts["verify_iat"] and "iat" in payload:
        if now + leeway < int(payload["iat"]):
            raise ValueError("Token used before issued")

    if issuer is not None and opts["verify_iss"]:
        if payload.get("iss") != issuer:
            raise ValueError("Invalid issuer")

    if audience is not None and opts["verify_aud"]:
        aud = payload.get("aud")
        if aud is None:
            raise ValueError("Missing audience")
        if isinstance(audience, (list, tuple, set)):
            if aud not in audience:
                raise ValueError("Invalid audience")
        else:
            if aud != audience:
                raise ValueError("Invalid audience")

    return payload
