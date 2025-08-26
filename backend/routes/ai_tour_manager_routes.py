from auth.dependencies import get_current_user_id, require_role

from flask import Blueprint, request, jsonify
from services.ai_tour_manager_service import AITourManagerService

ai_routes = Blueprint('ai_tour_routes', __name__)
ai_service = AITourManagerService(db=None)

@ai_routes.route('/ai/unlock', methods=['POST'])
def unlock_manager():
    data = request.json
    try:
        result = ai_service.unlock_ai_manager(data['band_id'])
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ai_routes.route('/ai/upgrade/<int:band_id>', methods=['POST'])
def upgrade_manager(band_id):
    try:
        result = ai_service.upgrade_manager(band_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@ai_routes.route('/ai/plan/<int:band_id>', methods=['POST'])
def plan_route(band_id):
    data = request.json
    try:
        result = ai_service.generate_optimized_route(band_id, data['cities'])
        return jsonify({'ordered_cities': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
