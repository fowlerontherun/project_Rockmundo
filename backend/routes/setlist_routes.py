from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

from backend.services import setlist_service


router = APIRouter()


class RevisionCreate(BaseModel):
    setlist: Any
    author: str


@router.post("/setlists/{setlist_id}/revisions")
def create_revision(setlist_id: int, payload: RevisionCreate):
    revision_id = setlist_service.create_revision(setlist_id, payload.setlist, payload.author)
    return {"id": revision_id, "status": "pending"}


@router.post("/setlists/{setlist_id}/revisions/{revision_id}/approve")
def approve_revision(setlist_id: int, revision_id: int):
    if not setlist_service.approve_revision(setlist_id, revision_id):
        raise HTTPException(status_code=404, detail="Revision not found")
    return {"status": "approved"}


@router.get("/setlists/{setlist_id}/revisions")
def list_revisions(setlist_id: int):
    return setlist_service.list_revisions(setlist_id)
