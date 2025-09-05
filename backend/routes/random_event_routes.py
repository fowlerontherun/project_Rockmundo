from flask import Blueprint, jsonify, request
from services.random_event_service import RandomEventService

event_routes = Blueprint("random_event_routes", __name__)
event_service = RandomEventService(db=None)


@event_routes.route("/events/trigger/<int:band_id>", methods=["POST"])
def trigger_event(band_id):
    """Trigger a context-aware event for a band.

    The request body can include optional ``location`` and ``mood`` fields to
    influence the selected event.  Possible event types include:

    * ``delay`` – Vehicle breakdown caused a delay.
    * ``press`` – Local press covered the band’s arrival.
    * ``fan_interaction`` – Fans welcomed the band at the venue.
    * ``local_cuisine`` – Sampled local cuisine, lifting spirits.
    """

    payload = request.get_json(silent=True) or {}
    location = payload.get("location")
    mood = payload.get("mood")
    try:
        result = event_service.trigger_event_for_band(
            band_id, location=location, mood=mood
        )
        return jsonify(result), 200
    except Exception as e:  # pragma: no cover - simple error pass-through
        return jsonify({"error": str(e)}), 500
