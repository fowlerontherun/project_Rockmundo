"""Seed data for onboarding questions."""

from backend.models.onboarding import Question, QuestionOption

# Define the first question with distinct options.
QUESTIONS: list[Question] = [
    Question(
        id=1,
        text="What did you get for Christmas at age 5?",
        options=[
            QuestionOption(text="Guitar", xp=10, stat="guitar", boost=1),
            QuestionOption(text="Microphone", xp=8, stat="vocals", boost=1),
            QuestionOption(text="Piano", xp=12, stat="piano", boost=1),
            QuestionOption(text="A laptop", xp=6, stat="songwriting", boost=1),
        ],
    ),
]

# Generate placeholder questions to reach a pool of 50.
for i in range(2, 51):
    QUESTIONS.append(
        Question(
            id=i,
            text=f"Sample question {i}?",
            options=[
                QuestionOption(text="Option A", xp=5, stat="guitar", boost=1),
                QuestionOption(text="Option B", xp=5, stat="vocals", boost=1),
                QuestionOption(text="Option C", xp=5, stat="piano", boost=1),
                QuestionOption(text="Option D", xp=5, stat="songwriting", boost=1),
            ],
        )
    )

__all__ = ["QUESTIONS"]
