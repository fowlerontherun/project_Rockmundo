import time
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import jwt


def _base_payload():
    now = int(time.time())
    return {"iss": "me", "aud": "you", "exp": now + 10}


def test_decode_valid_claims():
    token = jwt.encode(_base_payload(), "secret")
    data = jwt.decode(token, "secret", issuer="me", audience="you")
    assert data["aud"] == "you"


def test_decode_rejects_algorithm():
    token = jwt.encode(_base_payload(), "secret")
    with pytest.raises(ValueError, match="Algorithm not allowed"):
        jwt.decode(token, "secret", algorithms=["HS512"], issuer="me", audience="you")


def test_decode_validates_issuer_and_audience():
    token = jwt.encode(_base_payload(), "secret")
    with pytest.raises(ValueError, match="Invalid issuer"):
        jwt.decode(token, "secret", issuer="other", audience="you")
    with pytest.raises(ValueError, match="Invalid audience"):
        jwt.decode(token, "secret", issuer="me", audience="them")


def test_leeway_and_options_control_expiry():
    now = int(time.time())
    payload = {"iss": "me", "aud": "you", "exp": now - 2}
    token = jwt.encode(payload, "secret")

    with pytest.raises(ValueError, match="Token expired"):
        jwt.decode(token, "secret", issuer="me", audience="you")

    # Leeway allows short expiry drift
    jwt.decode(token, "secret", issuer="me", audience="you", leeway=5)

    # options can disable expiration verification entirely
    jwt.decode(
        token,
        "secret",
        issuer="me",
        audience="you",
        options={"verify_exp": False},
    )

