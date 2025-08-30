from backend.models.quest import Quest, QuestStage, QuestReward
from backend.services.quest_service import QuestService


def sample_quest():
    return Quest(
        id="q1",
        name="Test Quest",
        stages={
            "start": QuestStage(
                id="start",
                description="Start",
                branches={"left": "left_stage", "right": "right_stage"},
            ),
            "left_stage": QuestStage(
                id="left_stage",
                description="Left path",
                branches={},
                reward=QuestReward(type="xp", amount=10),
            ),
            "right_stage": QuestStage(
                id="right_stage",
                description="Right path",
                branches={},
                reward=QuestReward(type="item", amount=1),
            ),
        },
        initial_stage="start",
    )


def test_branching_logic():
    quest = sample_quest()
    service = QuestService()
    service.assign_quest(1, quest)
    stage = service.report_progress(1, quest, "left")
    assert stage.id == "left_stage"


def test_reward_distribution():
    quest = sample_quest()
    service = QuestService()
    service.assign_quest(1, quest)
    service.report_progress(1, quest, "right")
    reward = service.claim_reward(1, quest.id)
    assert reward.type == "item"
    assert reward.amount == 1
    assert service.claim_reward(1, quest.id) is None
