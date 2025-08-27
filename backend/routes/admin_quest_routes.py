from fastapi import APIRouter, HTTPException, Request, Depends

from auth.dependencies import get_current_user_id, require_role
from services.quest_admin_service import QuestAdminService
from services.admin_audit_service import audit_dependency

router = APIRouter(
    prefix="/quests", tags=["AdminQuests"], dependencies=[Depends(audit_dependency)]
)
svc = QuestAdminService()


@router.post("/")
async def create_quest(data: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    try:
        quest = svc.create_quest(
            name=data.get("name", "Unnamed"),
            stages=data.get("stages", []),
            initial_stage=data.get("initial_stage", ""),
        )
        return quest
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{quest_id}/stage/{stage_id}")
async def update_stage(quest_id: int, stage_id: str, data: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    try:
        stage = svc.update_stage(
            quest_id,
            stage_id,
            description=data.get("description"),
            branches=data.get("branches"),
            reward=data.get("reward"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    return stage


@router.post("/{quest_id}/version")
async def version_quest(quest_id: int, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    quest = svc.version_quest(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    return quest


@router.delete("/{quest_id}")
async def delete_quest(quest_id: int, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    svc.delete_quest(quest_id)
    return {"status": "deleted"}
