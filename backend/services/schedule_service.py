from typing import List, Dict

from backend.models import activity as activity_model
from backend.models import daily_schedule as schedule_model


class ScheduleService:
    """Service layer wrapping activity and daily schedule operations."""

    # Activity CRUD -----------------------------------------------------
    def create_activity(self, name: str, duration_hours: int, category: str) -> int:
        return activity_model.create_activity(name, duration_hours, category)

    def get_activity(self, activity_id: int) -> Dict | None:
        return activity_model.get_activity(activity_id)

    def update_activity(
        self, activity_id: int, name: str, duration_hours: int, category: str
    ) -> None:
        activity_model.update_activity(activity_id, name, duration_hours, category)

    def delete_activity(self, activity_id: int) -> None:
        activity_model.delete_activity(activity_id)

    # Schedule logic ----------------------------------------------------
    def schedule_activity(
        self, user_id: int, date: str, hour: int, activity_id: int
    ) -> None:
        schedule_model.add_entry(user_id, date, hour, activity_id)

    def update_schedule_entry(
        self, user_id: int, date: str, hour: int, activity_id: int
    ) -> None:
        schedule_model.update_entry(user_id, date, hour, activity_id)

    def remove_schedule_entry(self, user_id: int, date: str, hour: int) -> None:
        schedule_model.remove_entry(user_id, date, hour)

    def get_daily_schedule(self, user_id: int, date: str) -> List[Dict]:
        return schedule_model.get_schedule(user_id, date)


schedule_service = ScheduleService()

__all__ = ["ScheduleService", "schedule_service"]
