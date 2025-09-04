from auth.dependencies import get_current_user_id, require_role

from flask import Blueprint, request, jsonify
from services.karma_db import KarmaDB
from services.karma_service import KarmaService

karma_routes = Blueprint('karma_routes', __name__)
karma_service = KarmaService(KarmaDB())

@karma_routes.route('/karma/<int:user_id>', methods=['GET'])
def get_karma(user_id):
    return jsonify({
        "total": karma_service.get_user_karma(user_id),
        "history": karma_service.get_karma_history(user_id)
    })

@karma_routes.route('/karma/adjust', methods=['POST'])
def adjust_karma():
    data = request.json
    try:
        karma_service.adjust_karma(
            user_id=data['user_id'],
            amount=data['amount'],
            reason=data['reason'],
            source=data['source']
        )
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 400
