
from flask import Blueprint, request, jsonify
from services.random_event_service import RandomEventService

event_routes = Blueprint('random_event_routes', __name__)
event_service = RandomEventService(db=None)

@event_routes.route('/events/trigger/<int:band_id>', methods=['POST'])
def trigger_event(band_id):
    try:
        result = event_service.trigger_event_for_band(band_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
