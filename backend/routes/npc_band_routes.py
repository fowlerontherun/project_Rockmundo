from auth.dependencies import get_current_user_id, require_role

from flask import Blueprint, request, jsonify
from services.npc_band_service import NPCBandService

npc_routes = Blueprint('npc_band_routes', __name__)
npc_service = NPCBandService(db=None)

@npc_routes.route('/npc/create', methods=['POST'])
def create_npc_band():
    data = request.json
    try:
        result = npc_service.create_npc_band(
            name=data['name'],
            genre=data['genre']
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@npc_routes.route('/npc/simulate', methods=['POST'])
def simulate_npc_activity():
    try:
        npc_service.run_simulation_loop()
        return jsonify({'status': 'NPC simulation complete'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
