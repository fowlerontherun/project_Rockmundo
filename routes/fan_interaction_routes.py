from auth.dependencies import get_current_user_id, require_permission

from flask import Blueprint, request, jsonify
from services.fan_interaction_service import FanInteractionService

fan_routes = Blueprint('fan_routes', __name__)
fan_service = FanInteractionService(db=None)

@fan_routes.route('/fans/interact', methods=['POST'])
def record_fan_interaction():
    data = request.json
    try:
        result = fan_service.record_interaction(
            band_id=data['band_id'],
            fan_id=data['fan_id'],
            interaction_type=data['interaction_type'],
            content=data['content']
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@fan_routes.route('/fans/band/<int:band_id>', methods=['GET'])
def get_interactions(band_id):
    interaction_type = request.args.get('type')
    return jsonify(fan_service.get_band_interactions(band_id, interaction_type))

@fan_routes.route('/fans/petitions/summary', methods=['GET'])
def get_petition_summary():
    return jsonify(fan_service.get_petition_summary())
