
from flask import Blueprint, jsonify
from services.world_pulse_service import WorldPulseService

pulse_routes = Blueprint('pulse_routes', __name__)
pulse_service = WorldPulseService(db=None)

@pulse_routes.route('/world-pulse', methods=['GET'])
def get_world_pulse():
    try:
        result = pulse_service.generate_world_pulse()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
