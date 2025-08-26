from auth.dependencies import get_current_user_id, require_role

from flask import Blueprint, request, jsonify
from services.live_performance_service import LivePerformanceService

live_routes = Blueprint('live_routes', __name__)
live_service = LivePerformanceService(db=None)

@live_routes.route('/gigs/simulate', methods=['POST'])
def simulate_gig():
    data = request.json
    try:
        gig = live_service.simulate_gig(
            band_id=data['band_id'],
            city=data['city'],
            venue=data['venue'],
            setlist=data['setlist']
        )
        return jsonify(gig), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@live_routes.route('/gigs/band/<int:band_id>', methods=['GET'])
def get_band_gigs(band_id):
    return jsonify(live_service.get_band_performances(band_id))
