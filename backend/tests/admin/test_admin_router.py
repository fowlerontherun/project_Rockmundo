import asyncio
import pytest
from fastapi import HTTPException, Request

from backend.routes.admin_analytics_routes import kpis
from backend.routes.admin_job_routes import trigger_world_pulse_daily
from backend.routes.admin_media_moderation_routes import flag_media


def test_admin_sub_routes_require_admin_role():
    req = Request({})  # no auth headers

    with pytest.raises(HTTPException):
        asyncio.run(kpis(req, "2024-01-01", "2024-01-31"))

    with pytest.raises(HTTPException):
        asyncio.run(trigger_world_pulse_daily(req))

    with pytest.raises(HTTPException):
        asyncio.run(flag_media(123, req))

