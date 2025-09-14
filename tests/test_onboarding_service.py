from services.onboarding_question_service import OnboardingQuestionService


def test_get_questions_returns_three_unique_questions() -> None:
    service = OnboardingQuestionService()
    questions = service.get_questions()
    assert len(questions) == 3
    assert len({q.id for q in questions}) == 3


def test_evaluate_answers_accumulates_xp_and_stats() -> None:
    service = OnboardingQuestionService()
    questions = service.get_questions()
    answers = {q.id: 0 for q in questions}
    xp, boosts = service.evaluate_answers(answers)
    assert xp > 0
    assert boosts
