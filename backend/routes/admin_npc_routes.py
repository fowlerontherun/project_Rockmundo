from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth.dependencies import get_current_user_id, require_role
from backend.services.npc_service import NPCService
from backend.services.admin_audit_service import audit_dependency

router = APIRouter(
    prefix="/npcs", tags=["AdminNPCs"], dependencies=[Depends(audit_dependency)]
)
svc = NPCService()


@router.post("/")
async def create_npc(data: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    return svc.create_npc(
        identity=data.get("identity", "unknown"),
        npc_type=data.get("npc_type", "generic"),
        dialogue_hooks=data.get("dialogue_hooks"),
        stats=data.get("stats"),
    )


@router.put("/{npc_id}")
async def edit_npc(npc_id: int, data: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    npc = svc.update_npc(npc_id, **data)
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
    return npc


@router.delete("/{npc_id}")
async def delete_npc(npc_id: int, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    if not svc.delete_npc(npc_id):
        raise HTTPException(status_code=404, detail="NPC not found")
    return {"status": "deleted"}


@router.post("/preview")
async def preview_npc(data: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    return svc.preview_npc(
        identity=data.get("identity", "unknown"),
        npc_type=data.get("npc_type", "generic"),
        dialogue_hooks=data.get("dialogue_hooks"),
        stats=data.get("stats"),
    )


@router.post("/{npc_id}/simulate")
async def simulate_npc(npc_id: int, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    result = svc.simulate_npc(npc_id)
    if not result:
        raise HTTPException(status_code=404, detail="NPC not found")
    return result
