
from flask import Blueprint, request, jsonify
from services.band_relationship_service import BandRelationshipService

relationship_routes = Blueprint('relationship_routes', __name__)
relationship_service = BandRelationshipService(db=None)

@relationship_routes.route('/relationship/create', methods=['POST'])
def create_relationship():
    data = request.json
    try:
        result = relationship_service.create_relationship(
            band_a_id=data['band_a_id'],
            band_b_id=data['band_b_id'],
            relationship_type=data['type']
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@relationship_routes.route('/relationship/list/<int:band_id>', methods=['GET'])
def list_relationships(band_id):
    rel_type = request.args.get('type')
    try:
        result = relationship_service.get_relationships(band_id, rel_type)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@relationship_routes.route('/relationship/end', methods=['POST'])
def end_relationship():
    data = request.json
    try:
        result = relationship_service.end_relationship(
            band_a_id=data['band_a_id'],
            band_b_id=data['band_b_id']
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
