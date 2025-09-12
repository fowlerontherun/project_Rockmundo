from datetime import datetime
from typing import Any, Dict, List, Literal

from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator


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


class LearningSchema(BaseModel):
    xp_rate: int = Field(..., gt=0)
    level_cap: int = Field(..., ge=1)
    prerequisites: Dict[str, Any] | None = None

    @field_validator("prerequisites")
    def validate_prerequisites(cls, v: Dict[str, Any] | None) -> Dict[str, Any] | None:
        if v is not None and not v:
            raise ValueError("prerequisites_cannot_be_empty")
        return v


class CourseSchema(LearningSchema):
    skill_target: str
    duration: int
    prestige: bool = False


class BookSchema(LearningSchema):
    title: str
    genre: str
    rarity: str


class OnlineTutorialSchema(LearningSchema):
    video_url: str
    skill: str
    rarity_weight: int


class TutorSchema(LearningSchema):
    name: str
    specialization: str
    hourly_rate: int


class ApprenticeshipSchema(LearningSchema):
    student_id: int
    mentor_id: int
    mentor_type: str
    skill_id: int
    duration_days: int
    start_date: str | None = None
    status: str = "pending"


class WorkshopSchema(LearningSchema):
    name: str
    skill_target: str
    duration: int


router = APIRouter(prefix="/schema", tags=["AdminSchema"])


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


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



@router.get("/course")
async def course_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return CourseSchema.model_json_schema()

@router.get("/book")
async def book_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return BookSchema.model_json_schema()


@router.get("/online_tutorial")
async def online_tutorial_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return OnlineTutorialSchema.model_json_schema()


@router.get("/tutor")
async def tutor_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return TutorSchema.model_json_schema()


@router.get("/apprenticeship")
async def apprenticeship_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return ApprenticeshipSchema.model_json_schema()


@router.get("/workshop")
async def workshop_schema(req: Request) -> Dict[str, Any]:
    await _ensure_admin(req)
    return WorkshopSchema.model_json_schema()
