
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

@song_routes.route('/songs/<int:song_id>', methods=['PUT'])
def update_song(song_id):
    updates = request.json
    song_service.update_song(song_id, updates)
    return '', 204

@song_routes.route('/songs/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    song_service.delete_song(song_id)
    return '', 204
