from datetime import datetime

def fetch_user_metrics(filters):
    return {
        "DAU": 1247,
        "MAU": 8123,
        "retention_rate": "48%",
        "avg_session_time": "61 minutes",
        "login_streaks": {"1_day": 350, "7_day": 120, "30_day": 25},
        "filters": filters.dict()
    }

def fetch_economy_metrics(filters):
    return {
        "total_merch_sales": "$18,420",
        "skin_transactions": 614,
        "top_earner": "Band #4823 - $2,140",
        "royalties_paid": "$3,872",
        "active_marketplace_users": 388,
        "filters": filters.dict()
    }

def fetch_event_metrics(filters):
    return {
        "gigs_played_today": 672,
        "albums_released_week": 134,
        "top_genres": ["Pop", "Jazz", "Electro"],
        "most_used_skills": ["Electric Guitar", "Songwriting"],
        "filters": filters.dict()
    }

def fetch_community_metrics(filters):
    return {
        "avg_karma": 2.1,
        "reports_submitted": 4,
        "events_joined": 218,
        "alliances_formed": 39,
        "filters": filters.dict()
    }

def fetch_error_logs():
    return [
        {
            "timestamp": str(datetime.utcnow()),
            "endpoint": "/bands/create",
            "error_type": "ValidationError",
            "message": "Band name required"
        },
        {
            "timestamp": str(datetime.utcnow()),
            "endpoint": "/skins/purchase",
            "error_type": "TransactionError",
            "message": "Insufficient balance"
        }
    ]