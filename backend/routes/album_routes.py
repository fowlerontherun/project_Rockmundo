from flask import Blueprint, jsonify, request
from services.album_service import AlbumService

album_routes = Blueprint("album_routes", __name__)
album_service = AlbumService()

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

@album_routes.route("/albums/<int:release_id>", methods=["PUT"])
def update_release(release_id):
    updates = request.json
    result = album_service.update_release(release_id, updates)
    status = 404 if "error" in result else 200
    return jsonify(result), status

@album_routes.route("/albums/<int:release_id>/publish", methods=["POST"])
def publish_release(release_id):
    result = album_service.publish_release(release_id)
    status = 404 if "error" in result else 200
    return jsonify(result), status
