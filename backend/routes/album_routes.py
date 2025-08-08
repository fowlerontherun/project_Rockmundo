
from flask import Blueprint, request, jsonify
from services.album_service import AlbumService

album_routes = Blueprint('album_routes', __name__)
album_service = AlbumService(db=None)

@album_routes.route('/albums', methods=['POST'])
def create_album():
    data = request.json
    try:
        return jsonify(album_service.create_album(data)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@album_routes.route('/albums/band/<int:band_id>', methods=['GET'])
def get_band_albums(band_id):
    return jsonify(album_service.list_albums_by_band(band_id))

@album_routes.route('/albums/<int:album_id>', methods=['PUT'])
def update_album(album_id):
    updates = request.json
    album_service.update_album(album_id, updates)
    return '', 204

@album_routes.route('/albums/<int:album_id>/publish', methods=['POST'])
def publish_album(album_id):
    album_service.publish_album(album_id)
    return '', 200
