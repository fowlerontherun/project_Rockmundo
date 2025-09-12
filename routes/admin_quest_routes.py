from fastapi import APIRouter, Depends, HTTPException, Request

from auth.dependencies import get_current_user_id, require_permission
from services.quest_admin_service import QuestAdminService
from services.admin_audit_service import audit_dependency

router = APIRouter(
    prefix="/quests", tags=["AdminQuests"], dependencies=[Depends(audit_dependency)]
)
svc = QuestAdminService()


async def _require_admin(req: Request) -> int:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return admin_id


@router.post("/")
async def create_quest(data: dict, req: Request):
    await _require_admin(req)
    try:
        if "nodes" in data and "edges" in data:
            quest = svc.create_from_graph(data)
        else:
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
    await _require_admin(req)
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
    await _require_admin(req)
    quest = svc.version_quest(quest_id)
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    return quest


@router.delete("/{quest_id}")
async def delete_quest(quest_id: int, req: Request):
    await _require_admin(req)
    svc.delete_quest(quest_id)
    return {"status": "deleted"}


@router.post("/preview")
async def preview_quest(data: dict, req: Request):
    await _require_admin(req)
    try:
        preview = svc.preview_graph(data)
        return preview
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/validate")
async def validate_quest(data: dict, req: Request):
    await _require_admin(req)
    try:
        svc.validate_graph(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"valid": True}
