
from flask import Blueprint, request, jsonify
from services.tour_service import TourService

tour_routes = Blueprint('tour_routes', __name__)
tour_service = TourService(db=None)

@tour_routes.route('/tours', methods=['POST'])
def create_tour():
    data = request.json
    try:
        return jsonify(tour_service.create_tour(data)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@tour_routes.route('/tours/band/<int:band_id>', methods=['GET'])
def get_band_tours(band_id):
    return jsonify(tour_service.list_tours_by_band(band_id))

@tour_routes.route('/tours/<int:tour_id>/status', methods=['PUT'])
def update_tour_status(tour_id):
    data = request.json
    tour_service.update_tour_status(tour_id, data['status'])
    return '', 204

@tour_routes.route('/tours/<int:tour_id>', methods=['GET'])
def get_tour(tour_id):
    return jsonify(tour_service.get_tour(tour_id))
