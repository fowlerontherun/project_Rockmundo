"""Administrative routes for managing name datasets."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth.dependencies import get_current_user_id, require_permission
from services import name_dataset_service as dataset_service
from services.admin_audit_service import audit_dependency
from pydantic import BaseModel

router = APIRouter(
    prefix="/names", tags=["AdminNames"], dependencies=[Depends(audit_dependency)]
)


class FirstNameIn(BaseModel):
    name: str
    gender: Literal["male", "female"]


class SurnameIn(BaseModel):
    name: str


@router.post("/first")
async def add_first_name(payload: FirstNameIn, req: Request) -> dict[str, str]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    if not dataset_service.add_first_name(payload.name, payload.gender):
        raise HTTPException(status_code=409, detail="Name already exists")
    return {"status": "ok"}


@router.post("/surname")
async def add_surname(payload: SurnameIn, req: Request) -> dict[str, str]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    if not dataset_service.add_surname(payload.name):
        raise HTTPException(status_code=409, detail="Name already exists")
    return {"status": "ok"}
