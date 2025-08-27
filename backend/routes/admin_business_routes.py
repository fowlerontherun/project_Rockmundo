"""Administrative CRUD routes for businesses."""
from fastapi import APIRouter, HTTPException, Request

from auth.dependencies import get_current_user_id, require_role
from services.business_service import BusinessService

router = APIRouter(prefix="/businesses", tags=["AdminBusinesses"])
svc = BusinessService()


@router.post("/")
async def create_business(payload: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    return svc.create_business(
        owner_id=payload.get("owner_id"),
        name=payload.get("name", ""),
        business_type=payload.get("business_type", ""),
        location=payload.get("location", ""),
        startup_cost=int(payload.get("startup_cost", 0)),
        revenue_rate=int(payload.get("revenue_rate", 0)),
    )


@router.get("/")
async def list_businesses(req: Request, owner_id: int | None = None):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    return svc.list_businesses(owner_id)


@router.put("/{business_id}")
async def edit_business(business_id: int, payload: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    biz = svc.update_business(business_id, payload)
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    return biz


@router.delete("/{business_id}")
async def delete_business(business_id: int, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    if not svc.delete_business(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    return {"status": "deleted"}
