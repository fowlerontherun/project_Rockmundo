from flask import Blueprint, jsonify, request

from services.tournament_service import TournamentService


tournament_routes = Blueprint("tournament_routes", __name__)
service = TournamentService()


@tournament_routes.route("/tournaments", methods=["POST"])
def register_bands():
    data = request.get_json() or {}
    band_ids = data.get("band_ids", [])
    if not band_ids:
        return jsonify({"error": "band_ids required"}), 400
    tid = service.create_tournament(band_ids)
    return jsonify({"tournament_id": tid}), 201


@tournament_routes.route("/tournaments/<int:tid>/bracket", methods=["GET"])
def view_bracket(tid: int):
    bracket = service.get_bracket(tid)
    if not bracket:
        return jsonify({"error": "tournament not found"}), 404
    return jsonify(bracket.to_dict())


@tournament_routes.route("/tournaments/<int:tid>/results", methods=["POST"])
def report_results(tid: int):
    bracket = service.get_bracket(tid)
    if not bracket:
        return jsonify({"error": "tournament not found"}), 404
    champion = service.play_round(bracket)
    response = {"bracket": bracket.to_dict()}
    if champion is not None:
        response["champion"] = champion
    return jsonify(response)
