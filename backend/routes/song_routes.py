from auth.dependencies import get_current_user_id, require_role

from flask import Blueprint, request, jsonify
from services.song_service import SongService

song_routes = Blueprint('song_routes', __name__)
song_service = SongService(db=None)

@song_routes.route('/songs', methods=['POST'])
def create_song():
    data = request.json
    try:
        return jsonify(song_service.create_song(data)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@song_routes.route('/songs/band/<int:band_id>', methods=['GET'])
def get_band_songs(band_id):
    return jsonify(song_service.list_songs_by_band(band_id))


@song_routes.route('/songs/<int:song_id>/covers', methods=['GET'])
def get_song_covers(song_id):
    return jsonify(song_service.list_covers_of_song(song_id))


@song_routes.route('/cover_royalties/band/<int:band_id>', methods=['GET'])
def get_cover_royalties(band_id):
    """Return cover royalty transactions for a band."""
    return jsonify(song_service.list_cover_royalties(band_id))


@song_routes.route('/cover_royalties/band/<int:band_id>', methods=['POST'])
def upload_license(band_id):
    """Upload proof of a cover license and record payment."""
    song_id = int(request.form['song_id'])
    file = request.files.get('license_proof')
    proof_url = file.filename if file else request.form.get('license_proof_url', '')
    res = song_service.purchase_cover_license(song_id, band_id, proof_url)
    return jsonify(res), 201

@song_routes.route('/songs/<int:song_id>', methods=['PUT'])
def update_song(song_id):
    updates = request.json
    song_service.update_song(song_id, updates)
    return '', 204

@song_routes.route('/songs/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    song_service.delete_song(song_id)
    return '', 204
