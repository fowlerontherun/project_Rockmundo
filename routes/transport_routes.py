from backend.auth.dependencies import get_current_user_id, require_permission

from flask import Blueprint, request, jsonify
from services.transport_service import TransportService

transport_routes = Blueprint('transport_routes', __name__)
transport_service = TransportService(db=None)

@transport_routes.route('/transport/assign', methods=['POST'])
def assign_vehicle():
    data = request.json
    try:
        return jsonify(transport_service.assign_vehicle(data['band_id'], data['vehicle_type'])), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@transport_routes.route('/transport/band/<int:band_id>', methods=['GET'])
def get_band_vehicle(band_id):
    return jsonify(transport_service.get_band_vehicle(band_id))

@transport_routes.route('/transport/<int:vehicle_id>/maintain', methods=['PUT'])
def maintain_vehicle(vehicle_id):
    transport_service.update_maintenance(vehicle_id)
    return '', 204
