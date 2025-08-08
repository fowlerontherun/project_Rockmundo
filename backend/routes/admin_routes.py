
from flask import Blueprint, request, jsonify
from services.admin_service import AdminService

admin_routes = Blueprint('admin_routes', __name__)
admin_service = AdminService(db=None)

@admin_routes.route('/admin/log', methods=['POST'])
def log_action():
    data = request.json
    try:
        result = admin_service.log_action(
            admin_id=data['admin_id'],
            action_type=data['action_type'],
            payload=data['payload']
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@admin_routes.route('/admin/reset-world', methods=['POST'])
def reset_world():
    try:
        result = admin_service.reset_world()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_routes.route('/admin/add-location', methods=['POST'])
def add_location():
    data = request.json
    try:
        result = admin_service.add_location(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@admin_routes.route('/admin/update-balance', methods=['POST'])
def update_balance():
    data = request.json
    try:
        result = admin_service.update_balancing(data['setting_name'], data['value'])
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
