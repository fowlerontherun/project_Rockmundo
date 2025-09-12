"""Pydantic schemas for onboarding questions."""

from typing import Dict, List

from pydantic import BaseModel


class QuestionOptionSchema(BaseModel):
    text: str
    xp: int
    stat: str
    boost: int


class QuestionSchema(BaseModel):
    id: int
    text: str
    options: List[QuestionOptionSchema]


class AnswersSchema(BaseModel):
    answers: Dict[int, int]


class EvaluationResponse(BaseModel):
    xp: int
    stat_boosts: Dict[str, int]
