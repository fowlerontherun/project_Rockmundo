# File: backend/auth/jwt.py
"""JWT helper utilities using PyJWT.

This module provides thin wrappers around the `PyJWT` library so the rest of
the code base can create and verify JSON Web Tokens without depending on a
custom implementation.  All token creation and validation should flow through
these helpers to ensure consistent behaviour across the application.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import jwt

DEFAULT_ALGORITHM = "HS256"


def encode(payload: Dict[str, Any], secret: str, *, algorithm: str = DEFAULT_ALGORITHM) -> str:
    """Encode a payload into a JWT string."""

    return jwt.encode(payload, secret, algorithm=algorithm)


def decode(
    token: str,
    secret: str,
    *,
    verify_exp: bool = True,
    leeway: int = 0,
    expected_iss: Optional[str] = None,
    expected_aud: Optional[str] = None,
    algorithms: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Decode a JWT token and return the payload.

    Parameters mirror the previous custom implementation so existing callers
    can continue to supply issuer/audience expectations and control expiration
    verification.
    """

    return jwt.decode(
        token,
        secret,
        algorithms=algorithms or [DEFAULT_ALGORITHM],
        issuer=expected_iss,
        audience=expected_aud,
        leeway=leeway,
        options={"verify_exp": verify_exp},
    )


def now_ts() -> int:
    """Return the current UTC timestamp as an integer."""

    return int(time.time())

