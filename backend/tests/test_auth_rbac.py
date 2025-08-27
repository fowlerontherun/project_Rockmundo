import asyncio
import pytest
from fastapi import HTTPException, Request

from routes.admin_job_routes import trigger_world_pulse_daily


def test_unauthenticated_requests_are_401():
    with pytest.raises(HTTPException):
        asyncio.run(trigger_world_pulse_daily(Request({})))

