"""Administrative CRUD routes for businesses."""
from fastapi import APIRouter, HTTPException, Request, Depends

from backend.auth.dependencies import get_current_user_id, require_permission
from services.business_service import BusinessService
from services.admin_audit_service import audit_dependency

router = APIRouter(
    prefix="/businesses", tags=["AdminBusinesses"], dependencies=[Depends(audit_dependency)]
)
svc = BusinessService()


@router.post("/")
async def create_business(payload: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
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
    await require_permission(["admin"], admin_id)
    return svc.list_businesses(owner_id)


@router.put("/{business_id}")
async def edit_business(business_id: int, payload: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    biz = svc.update_business(business_id, payload)
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    return biz


@router.delete("/{business_id}")
async def delete_business(business_id: int, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    if not svc.delete_business(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    return {"status": "deleted"}
