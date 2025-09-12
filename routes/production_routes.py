from flask import Blueprint, jsonify, request

from services.analytics_service import AnalyticsService
from services.economy_service import EconomyService
from services.production_service import ProductionService


production_routes = Blueprint("production_routes", __name__)
service = ProductionService(EconomyService(), AnalyticsService())


@production_routes.route("/tracks", methods=["POST"])
def create_track():
    data = request.json
    track = service.create_track(
        data["title"], data["band_id"], data["duration_sec"]
    )
    return jsonify(track.to_dict()), 201


@production_routes.route("/tracks/<int:track_id>/sessions", methods=["POST"])
def schedule_session(track_id: int):
    data = request.json
    session = service.schedule_session(
        track_id,
        data["scheduled_date"],
        data["engineer"],
        data["hours"],
        data["hourly_rate_cents"],
    )
    return jsonify(session.to_dict()), 201


@production_routes.route("/tracks/<int:track_id>/mix", methods=["POST"])
def mix_track(track_id: int):
    data = request.json
    mix = service.mix_track(
        track_id, data["engineer"], data["cost_cents"], data.get("mastered", True)
    )
    return jsonify(mix.to_dict()), 201


@production_routes.route("/tracks/<int:track_id>/release", methods=["POST"])
def release_track(track_id: int):
    data = request.json
    release = service.release_track(
        track_id,
        data["release_date"],
        data.get("channels", []),
        data["price_cents"],
        data["sales"],
    )
    return jsonify(release.to_dict()), 201


@production_routes.route("/tracks/<int:track_id>", methods=["GET"])
def get_track(track_id: int):
    track = service.get_track(track_id)
    if not track:
        return jsonify({"error": "not found"}), 404
    return jsonify(track.to_dict())

