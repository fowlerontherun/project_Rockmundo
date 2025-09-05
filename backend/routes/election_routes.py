from flask import Blueprint, jsonify, request
from services.election_service import ElectionService
from services.festival_builder_service import FestivalBuilderService

election_routes = Blueprint('election_routes', __name__)
election_service = ElectionService(db=None)
festival_builder_service = FestivalBuilderService()

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


@election_routes.route('/festival/proposals', methods=['POST'])
def create_festival_proposal():
    data = request.json
    try:
        proposal_id = festival_builder_service.propose_festival(
            proposer_id=data['proposer_id'],
            name=data['name'],
            description=data.get('description'),
        )
        return jsonify({'proposal_id': proposal_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@election_routes.route('/festival/proposals', methods=['GET'])
def list_festival_proposals():
    proposals = festival_builder_service.list_proposals()
    return jsonify([p.dict() for p in proposals]), 200


@election_routes.route('/festival/proposals/<int:proposal_id>/vote', methods=['POST'])
def vote_on_festival_proposal(proposal_id):
    data = request.json
    try:
        votes = festival_builder_service.vote_on_proposal(
            proposal_id=proposal_id,
            voter_id=data['voter_id'],
        )
        return jsonify({'votes': votes}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
