from backend.auth.dependencies import get_current_user_id, require_permission

from flask import Blueprint, request, jsonify
from services.tour_logistics_service import TourLogisticsService

tour_routes = Blueprint('tour_routes', __name__)
tour_service = TourLogisticsService(db=None)

@tour_routes.route('/tour/vehicles/register', methods=['POST'])
def register_vehicle():
    data = request.json
    try:
        result = tour_service.register_vehicle(
            band_id=data['band_id'],
            type=data['type'],
            capacity=data['capacity'],
            perks=data.get('perks', '')
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@tour_routes.route('/tour/routes/plan', methods=['POST'])
def plan_route():
    data = request.json
    try:
        result = tour_service.plan_route(
            band_id=data['band_id'],
            vehicle_id=data['vehicle_id'],
            origin=data['origin'],
            destination=data['destination'],
            hours=data['hours'],
            cost=data['cost']
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@tour_routes.route('/tour/routes/band/<int:band_id>', methods=['GET'])
def get_band_routes(band_id):
    return jsonify(tour_service.get_band_routes(band_id))

@tour_routes.route('/tour/vehicles/band/<int:band_id>', methods=['GET'])
def get_band_vehicles(band_id):
    return jsonify(tour_service.get_band_vehicles(band_id))
