from auth.dependencies import get_current_user_id, require_permission

from flask import Blueprint, request, jsonify
from services.stream_service import StreamService

stream_routes = Blueprint('stream_routes', __name__)
stream_service = StreamService(db=None)

@stream_routes.route('/streams', methods=['POST'])
def record_stream():
    data = request.json
    try:
        return jsonify(stream_service.record_stream(data)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@stream_routes.route('/streams/song/<int:song_id>', methods=['GET'])
def get_song_streams(song_id):
    return jsonify(stream_service.get_song_streams(song_id))

@stream_routes.route('/revenue/band/<int:band_id>', methods=['GET'])
def get_band_revenue(band_id):
    return jsonify(stream_service.get_band_revenue(band_id))
