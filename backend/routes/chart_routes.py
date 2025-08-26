from auth.dependencies import get_current_user_id, require_role

from flask import Blueprint, request, jsonify
from services.chart_service import ChartService

chart_routes = Blueprint('chart_routes', __name__)
chart_service = ChartService(db=None)

@chart_routes.route('/charts/global/<week_start>', methods=['GET'])
def get_global_chart(week_start):
    return jsonify(chart_service.get_chart("Global Top 100", week_start))

@chart_routes.route('/charts/recalculate', methods=['POST'])
def recalculate_charts():
    try:
        chart_service.calculate_weekly_charts()
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500
