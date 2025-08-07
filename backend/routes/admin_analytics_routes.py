from fastapi import APIRouter
from services.admin_analytics_service import *
from schemas.admin_analytics_schemas import AnalyticsFilterSchema

router = APIRouter()

@router.post("/admin/analytics/user_metrics")
def get_user_metrics(filters: AnalyticsFilterSchema):
    return fetch_user_metrics(filters)

@router.post("/admin/analytics/economy_metrics")
def get_economy_metrics(filters: AnalyticsFilterSchema):
    return fetch_economy_metrics(filters)

@router.post("/admin/analytics/event_metrics")
def get_event_metrics(filters: AnalyticsFilterSchema):
    return fetch_event_metrics(filters)

@router.post("/admin/analytics/community_metrics")
def get_community_metrics(filters: AnalyticsFilterSchema):
    return fetch_community_metrics(filters)

@router.get("/admin/analytics/error_logs")
def get_error_logs():
    return fetch_error_logs()