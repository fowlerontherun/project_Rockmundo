from models.quest import Quest, QuestStage, QuestReward


def get_seed_quests():
    """Return a list of predefined quests used for seeding the database."""
    return [
        Quest(
            id="first_gig",
            name="Play Your First Gig",
            stages={
                "start": QuestStage(
                    id="start",
                    description="Find a venue willing to host your band.",
                    branches={"book": "perform"},
                ),
                "perform": QuestStage(
                    id="perform",
                    description="Put on an unforgettable show.",
                    branches={},
                    reward=QuestReward(type="fame", amount=10),
                ),
            },
            initial_stage="start",
        )
    ]
