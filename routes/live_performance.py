from auth.dependencies import get_current_user_id, require_permission

from flask import Blueprint, request, jsonify
from services import live_performance_service
from services.notifications_service import NotificationsService

live_routes = Blueprint('live_routes', __name__)
notif_svc = NotificationsService()

@live_routes.route('/gigs/simulate', methods=['POST'])
def simulate_gig():
    data = request.json
    try:
        revision_id = data.get('revision_id')
        if revision_id is None:
            return jsonify({'error': 'revision_id required'}), 400
        gig = live_performance_service.simulate_gig(
            band_id=data['band_id'],
            city=data['city'],
            venue=data['venue'],
            setlist_revision_id=revision_id
        )
        try:
            user_id = data.get('user_id')
            if user_id:
                notif_svc.create(
                    user_id,
                    "Gig performed",
                    f"{data['city']} - {data['venue']}",
                    type_="gig",
                )
        except Exception:
            pass
        return jsonify(gig), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@live_routes.route('/gigs/band/<int:band_id>', methods=['GET'])
def get_band_gigs(band_id):
    return jsonify(live_performance_service.get_band_performances(band_id))
