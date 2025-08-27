from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Dict, Any, List

from auth.dependencies import get_current_user_id, require_role



class NPCSchema(BaseModel):
    identity: str
    npc_type: str
    dialogue_hooks: Dict[str, str] = {}
    stats: Dict[str, Any] = {}


class QuestStageSchema(BaseModel):
    id: str
    description: str
    branches: Dict[str, str] = {}
    reward: Dict[str, Any] | None = None


class QuestSchema(BaseModel):
    name: str
    initial_stage: str
    stages: List[QuestStageSchema]


class EconomyConfigSchema(BaseModel):
    tax_rate: float | None = None
    inflation_rate: float | None = None
    payout_rate: int | None = None


router = APIRouter(prefix="/schema", tags=["AdminSchema"])


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)


@router.get("/npc")
async def npc_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return NPCSchema.model_json_schema()


@router.get("/quest")
async def quest_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return QuestSchema.model_json_schema()


@router.get("/economy")
async def economy_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return EconomyConfigSchema.model_json_schema()
