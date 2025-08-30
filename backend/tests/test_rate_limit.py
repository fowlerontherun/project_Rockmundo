import asyncio

import pytest
from middleware.rate_limit import RateLimitMiddleware

from fastapi import HTTPException


class DummyClient:
    def __init__(self, host: str = "test") -> None:
        self.host = host


class DummyRequest:
    def __init__(self, host: str = "test") -> None:
        self.client = DummyClient(host)


async def _ok(_req):
    return "ok"


def test_rate_limit_blocks_after_limit() -> None:
    mw = RateLimitMiddleware(limit=2, backend="memory")
    req = DummyRequest(host="1.2.3.4")

    assert asyncio.run(mw.dispatch(req, _ok)) == "ok"
    assert asyncio.run(mw.dispatch(req, _ok)) == "ok"

    with pytest.raises(HTTPException):
        asyncio.run(mw.dispatch(req, _ok))

