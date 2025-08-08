
from models.admin_action import AdminAction
from datetime import datetime

class AdminService:
    def __init__(self, db):
        self.db = db

    def log_action(self, admin_id, action_type, payload):
        action = AdminAction(
            id=None,
            admin_id=admin_id,
            action_type=action_type,
            payload=payload
        )
        self.db.insert_admin_action(action)
        return action.to_dict()

    def reset_world(self):
        self.db.clear_all_data()
        return {"status": "World reset complete."}

    def add_location(self, location_data):
        self.db.insert_location(location_data)
        return {"status": "Location added."}

    def update_balancing(self, setting_name, value):
        self.db.update_game_balance(setting_name, value)
        return {"status": f"{setting_name} updated to {value}."}
