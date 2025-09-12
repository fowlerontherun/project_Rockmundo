from auth.dependencies import get_current_user_id, require_permission
# File: backend/routes/health_routes.py
from fastapi import APIRouter, Depends
from utils.db import get_conn

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/db")
def db_health():
    with get_conn() as conn:
        row = conn.execute("SELECT datetime('now') AS now").fetchone()
        return {"ok": True, "db_time": row["now"]}

@router.get("/ping")
def ping():
    return {"ok": True}
