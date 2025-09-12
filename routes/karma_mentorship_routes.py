from backend.auth.dependencies import get_current_user_id, require_permission

from flask import Blueprint, request, jsonify
from services.karma_mentorship_service import KarmaMentorshipService

karma_routes = Blueprint('karma_routes', __name__)
karma_service = KarmaMentorshipService(db=None)

@karma_routes.route('/karma/adjust', methods=['POST'])
def adjust_karma():
    data = request.json
    try:
        result = karma_service.adjust_karma(data['user_id'], data['delta'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@karma_routes.route('/mentorship/start', methods=['POST'])
def start_mentorship():
    data = request.json
    try:
        result = karma_service.start_mentorship(data['mentor_id'], data['mentee_id'])
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@karma_routes.route('/mentorship/end', methods=['POST'])
def end_mentorship():
    data = request.json
    try:
        result = karma_service.end_mentorship(data['mentor_id'], data['mentee_id'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
