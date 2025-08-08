
from flask import Blueprint, request, jsonify
from services.fame_service import FameService

fame_routes = Blueprint('fame_routes', __name__)
fame_service = FameService(db=None)

@fame_routes.route('/fame/<int:band_id>', methods=['GET'])
def get_fame_history(band_id):
    return jsonify(fame_service.get_fame_history(band_id))

@fame_routes.route('/fame/<int:band_id>/total', methods=['GET'])
def get_total_fame(band_id):
    return jsonify({"fame": fame_service.get_total_fame(band_id)})

@fame_routes.route('/fame/award', methods=['POST'])
def award_fame():
    data = request.json
    try:
        fame_service.award_fame(
            band_id=data['band_id'],
            source=data['source'],
            amount=data['amount'],
            reason=data['reason']
        )
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 400
