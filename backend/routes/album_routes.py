from auth.dependencies import get_current_user_id, require_role

from flask import Blueprint, request, jsonify
from services.album_service import AlbumService

album_routes = Blueprint('album_routes', __name__)
album_service = AlbumService(db=None)

@album_routes.route('/albums', methods=['POST'])
def create_release():
    data = request.json
    try:
        return jsonify(album_service.create_release(data)), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@album_routes.route('/albums/band/<int:band_id>', methods=['GET'])
def get_band_releases(band_id):
    return jsonify(album_service.list_releases_by_band(band_id))

@album_routes.route('/albums/<int:release_id>', methods=['PUT'])
def update_release(release_id):
    updates = request.json
    album_service.update_release(release_id, updates)
    return '', 204

@album_routes.route('/albums/<int:release_id>/publish', methods=['POST'])
def publish_release(release_id):
    album_service.publish_release(release_id)
    return '', 200
