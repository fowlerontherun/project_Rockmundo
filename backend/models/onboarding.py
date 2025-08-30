from dataclasses import dataclass


@dataclass
class QuestionOption:
    """Represents a possible answer to a question."""

    text: str
    xp: int
    stat: str
    boost: int


@dataclass
class Question:
    """A character creation question with four options."""

    id: int
    text: str
    options: list[QuestionOption]
