"""Routes for onboarding questionnaire."""

from fastapi import APIRouter

from backend.schemas.onboarding import (
    AnswersSchema,
    EvaluationResponse,
    QuestionSchema,
)
from services.onboarding_question_service import OnboardingQuestionService

router = APIRouter()
service = OnboardingQuestionService()


@router.get("/questions", response_model=list[QuestionSchema])
def get_questions() -> list[QuestionSchema]:
    """Return three random onboarding questions."""
    return service.get_questions()


@router.post("/answers", response_model=EvaluationResponse)
def submit_answers(payload: AnswersSchema) -> EvaluationResponse:
    """Evaluate provided answers and return XP/stat gains."""
    xp, boosts = service.evaluate_answers(payload.answers)
    return EvaluationResponse(xp=xp, stat_boosts=boosts)
