# startup.py
"""
If you want periodic schedules, you can enable them here.
By default, this only registers jobs (manual trigger via admin endpoints).
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI

from backend.core.scheduler import register_jobs, run_job

logger = logging.getLogger(__name__)


async def periodic() -> None:
    while True:
        for job in ("cleanup_idempotency", "cleanup_rate_limits"):
            try:
                result = await run_job(job)
                if not result.get("ok"):
                    logger.error(
                        "scheduled job %s failed: %s", job, result.get("error")
                    )
            except Exception:
                logger.exception("error running scheduled job %s", job)
        await asyncio.sleep(6 * 60 * 60)  # every 6 hours


def setup_scheduler(app: FastAPI) -> None:
    register_jobs()
    app.add_event_handler("startup", lambda: asyncio.create_task(periodic()))
