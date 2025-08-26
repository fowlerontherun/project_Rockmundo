# startup.py
"""
If you want periodic schedules, you can enable them here.
By default, this only registers jobs (manual trigger via admin endpoints).
"""

from __future__ import annotations
import asyncio
from typing import Awaitable, Callable
from fastapi import FastAPI

from backend.core.scheduler import register_jobs, run_job

def setup_scheduler(app: FastAPI) -> None:
    register_jobs()

    # Example periodic tasks (commented out by default):
    # async def periodic() -> None:
    #     while True:
    #         try:
    #             await run_job("cleanup_idempotency")
    #             await run_job("cleanup_rate_limits")
    #         except Exception:
    #             pass
    #         await asyncio.sleep(6 * 60 * 60)  # every 6 hours
    #
    # app.add_event_handler("startup", lambda: asyncio.create_task(periodic()))
