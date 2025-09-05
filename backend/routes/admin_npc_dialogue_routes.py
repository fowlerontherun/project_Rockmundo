from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth.dependencies import get_current_user_id, require_permission
from backend.routes.admin_npc_routes import svc
from backend.services.admin_audit_service import audit_dependency

router = APIRouter(
    prefix="/npcs/dialogue", tags=["AdminNPCDialogue"], dependencies=[Depends(audit_dependency)]
)


@router.put("/{npc_id}")
async def edit_dialogue(npc_id: int, tree: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    result = svc.edit_dialogue(npc_id, tree)
    if not result:
        raise HTTPException(status_code=404, detail="NPC not found")
    return result


@router.post("/{npc_id}/preview")
async def preview_dialogue(npc_id: int, data: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    choices = data.get("choices", [])
    result = svc.preview_dialogue(npc_id, choices)
    if result is None:
        raise HTTPException(status_code=404, detail="NPC not found")
    return {"lines": result}
