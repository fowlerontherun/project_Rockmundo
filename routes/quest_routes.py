from fastapi import APIRouter, HTTPException, Depends
from auth.character_dependencies import get_current_character_id
from pydantic import BaseModel

from services.quest_service import QuestService
from backend.models.quest import QuestStage, QuestReward


quest_routes = APIRouter()
quest_service = QuestService()


class UserRequest(BaseModel):
    user_id: int


class ProgressRequest(UserRequest):
    choice: str


@quest_routes.post("/quests/start/{quest_id}", response_model=QuestStage)
def start_quest(quest_id: int, payload: UserRequest, character_id: int = Depends(get_current_character_id)):
    if payload.user_id != character_id:
        raise HTTPException(status_code=403, detail="Quest belongs to the selected character")
    try:
        quest = quest_service.load_quest(quest_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="quest not found")
    quest_service.assign_quest(character_id, quest)
    stage = quest.get_stage(quest.initial_stage)
    return stage


@quest_routes.post("/quests/progress/{quest_id}", response_model=QuestStage)
def report_progress(quest_id: int, payload: ProgressRequest, character_id: int = Depends(get_current_character_id)):
    if payload.user_id != character_id:
        raise HTTPException(status_code=403, detail="Quest belongs to the selected character")
    try:
        quest = quest_service.load_quest(quest_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="quest not found")
    try:
        stage = quest_service.report_progress(character_id, quest, payload.choice)
        return stage
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@quest_routes.post("/quests/claim/{quest_id}", response_model=QuestReward)
def claim_reward(quest_id: int, payload: UserRequest, character_id: int = Depends(get_current_character_id)):
    if payload.user_id != character_id:
        raise HTTPException(status_code=403, detail="Quest belongs to the selected character")
    reward = quest_service.claim_reward(character_id, str(quest_id))
    if reward:
        return reward
    raise HTTPException(status_code=404, detail="no reward")

