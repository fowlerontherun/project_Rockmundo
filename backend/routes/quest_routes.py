from flask import Blueprint, jsonify, request

from services.quest_service import QuestService
from seeds.quest_data import get_seed_quests

quest_routes = Blueprint("quest_routes", __name__)
quest_service = QuestService()
QUESTS = {quest.id: quest for quest in get_seed_quests()}


@quest_routes.route("/quests/start/<quest_id>", methods=["POST"])
def start_quest(quest_id):
    data = request.get_json()
    user_id = data["user_id"]
    quest = QUESTS.get(quest_id)
    if quest is None:
        return jsonify({"error": "quest not found"}), 404
    quest_service.assign_quest(user_id, quest)
    stage = quest.get_stage(quest.initial_stage)
    return jsonify(stage.dict()), 200


@quest_routes.route("/quests/progress/<quest_id>", methods=["POST"])
def report_progress(quest_id):
    data = request.get_json()
    user_id = data["user_id"]
    choice = data["choice"]
    quest = QUESTS.get(quest_id)
    if quest is None:
        return jsonify({"error": "quest not found"}), 404
    try:
        stage = quest_service.report_progress(user_id, quest, choice)
        return jsonify(stage.dict()), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@quest_routes.route("/quests/claim/<quest_id>", methods=["POST"])
def claim_reward(quest_id):
    data = request.get_json()
    user_id = data["user_id"]
    reward = quest_service.claim_reward(user_id, quest_id)
    if reward:
        return jsonify(reward.dict()), 200
    return jsonify({"error": "no reward"}), 404
