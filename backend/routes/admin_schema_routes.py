from datetime import datetime
from typing import Any, Dict, List, Literal

from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Request

from pydantic import BaseModel


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


class XPConfigSchema(BaseModel):
    daily_cap: int | None = None
    new_player_multiplier: float | None = None
    rested_xp_rate: float | None = None


class XPEventSchema(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime
    multiplier: float
    skill_target: str | None = None


class XPItemSchema(BaseModel):
    name: str
    effect_type: Literal["flat", "boost"]
    amount: float
    duration: int


class ItemSchema(BaseModel):
    name: str
    category: str
    stats: Dict[str, float] = {}


class BookSchema(BaseModel):
    title: str
    genre: str
    rarity: str
    max_skill_level: int


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


@router.get("/xp")
async def xp_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return XPConfigSchema.model_json_schema()


@router.get("/xp_event")
async def xp_event_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return XPEventSchema.model_json_schema()


@router.get("/xp_item")
async def xp_item_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return XPItemSchema.model_json_schema()


@router.get("/item")
async def item_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return ItemSchema.model_json_schema()


@router.get("/book")
async def book_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return BookSchema.model_json_schema()
