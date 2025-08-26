# jobs_routes.py
"""
Admin endpoints to list jobs, trigger a run, and view last results.

Mount these under your existing /admin routes group, e.g.:
app.include_router(router, prefix="/admin", tags=["admin"])

RBAC: Protect with your existing auth dependencies (not included here).
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Any

from backend.core.scheduler import register_jobs, list_jobs, run_job

router = APIRouter()

# Ensure registry is populated on import
register_jobs()


@router.get("/jobs", summary="List available jobs & last results")
async def get_jobs() -> Any:
    return list_jobs()


@router.post("/jobs/{job_name}/run", summary="Trigger a job now")
async def post_run_job(job_name: str) -> Any:
    result = await run_job(job_name)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "Job failed"))
    return result
