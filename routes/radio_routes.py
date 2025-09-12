from __future__ import annotations

"""API routes for radio stations and streaming."""

from flask import Blueprint, jsonify, request

from services.radio_service import RadioService

radio_routes = Blueprint("radio_routes", __name__)
_service = RadioService()
_service.ensure_schema()


@radio_routes.route("/radio/stations", methods=["POST"])
def create_station():
    data = request.get_json() or {}
    owner_id = int(data["owner_id"])
    name = data["name"]
    return jsonify(_service.create_station(owner_id, name)), 201


@radio_routes.route("/radio/stations/<int:station_id>/schedule", methods=["POST"])
def schedule_show(station_id: int):
    data = request.get_json() or {}
    title = data["title"]
    start_time = data["start_time"]
    return jsonify(_service.schedule_show(station_id, title, start_time)), 201


@radio_routes.route("/radio/stations/<int:station_id>/subscribe", methods=["POST"])
def subscribe(station_id: int):
    data = request.get_json() or {}
    user_id = int(data["user_id"])
    _service.subscribe(station_id, user_id)
    return jsonify({"status": "subscribed"})


@radio_routes.route("/radio/stations/<int:station_id>/listen", methods=["POST"])
def listen(station_id: int):
    data = request.get_json() or {}
    user_id = int(data["user_id"])
    try:
        count = _service.listen(station_id, user_id)
        return jsonify({"listeners": count})
    except PermissionError:
        return jsonify({"error": "not subscribed"}), 403
