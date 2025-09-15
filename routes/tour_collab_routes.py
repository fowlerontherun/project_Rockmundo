from typing import List, Dict, Optional
import json
import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import DB_PATH

router = APIRouter(prefix="/tour-collab", tags=["TourCollab"])


class CollaborationCreate(BaseModel):
    band_ids: List[int]
    setlist: List[dict] = []
    revenue_split: Dict[int, float] = {}
    schedule: List[dict] = []
    expenses: List[dict] = []


class InviteIn(BaseModel):
    band_id: int
    share: Optional[float] = None


@router.post("/")
def create_collaboration(payload: CollaborationCreate):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tour_collaborations (band_ids, setlist, revenue_split, schedule, expenses)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                json.dumps(payload.band_ids),
                json.dumps(payload.setlist),
                json.dumps(payload.revenue_split),
                json.dumps(payload.schedule),
                json.dumps(payload.expenses),
            ),
        )
        collab_id = cur.lastrowid
    return {"id": collab_id, **payload.dict()}


@router.post("/{collab_id}/invite")
def invite_band(collab_id: int, payload: InviteIn):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT band_ids, revenue_split FROM tour_collaborations WHERE id = ?",
            (collab_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Collaboration not found")
        band_ids = json.loads(row[0])
        revenue_split = json.loads(row[1])
        if payload.band_id in band_ids:
            raise HTTPException(status_code=400, detail="Band already added")
        band_ids.append(payload.band_id)
        if payload.share is not None:
            revenue_split[str(payload.band_id)] = payload.share
        cur.execute(
            "UPDATE tour_collaborations SET band_ids = ?, revenue_split = ? WHERE id = ?",
            (json.dumps(band_ids), json.dumps(revenue_split), collab_id),
        )
    return {"id": collab_id, "band_ids": band_ids, "revenue_split": revenue_split}


@router.get("/{collab_id}")
def get_collaboration(collab_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT band_ids, setlist, revenue_split, schedule, expenses FROM tour_collaborations WHERE id = ?",
            (collab_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Collaboration not found")
    return {
        "id": collab_id,
        "band_ids": json.loads(row[0]),
        "setlist": json.loads(row[1]),
        "revenue_split": json.loads(row[2]),
        "schedule": json.loads(row[3]) if row[3] else [],
        "expenses": json.loads(row[4]) if row[4] else [],
    }


@router.put("/{collab_id}")
def update_collaboration(collab_id: int, payload: CollaborationCreate):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE tour_collaborations SET band_ids=?, setlist=?, revenue_split=?, schedule=?, expenses=? WHERE id=?",
            (
                json.dumps(payload.band_ids),
                json.dumps(payload.setlist),
                json.dumps(payload.revenue_split),
                json.dumps(payload.schedule),
                json.dumps(payload.expenses),
                collab_id,
            ),
        )
    return {"id": collab_id, **payload.dict()}
