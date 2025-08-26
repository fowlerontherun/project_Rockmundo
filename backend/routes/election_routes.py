from auth.dependencies import get_current_user_id, require_role

from flask import Blueprint, request, jsonify
from services.election_service import ElectionService

election_routes = Blueprint('election_routes', __name__)
election_service = ElectionService(db=None)

@election_routes.route('/elections/create', methods=['POST'])
def create_election():
    data = request.json
    try:
        result = election_service.create_election(
            role_name=data['role_name'],
            candidates=data['candidates']
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@election_routes.route('/elections/vote', methods=['POST'])
def vote():
    data = request.json
    try:
        result = election_service.vote(
            election_id=data['election_id'],
            candidate_id=data['candidate_id']
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@election_routes.route('/elections/close/<int:election_id>', methods=['POST'])
def close_election(election_id):
    try:
        result = election_service.close_election(election_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
