"""Pydantic models and helper utilities for notifications."""

from pydantic import BaseModel
from typing import Optional

from services.notifications_service import NotificationsService


class Notification(BaseModel):
    user_id: int
    message: str
    type: Optional[str] = "info"
    timestamp: Optional[str]


class ScheduledEvent(BaseModel):
    user_id: int
    event_type: str
    description: str
    scheduled_time: str


# Global service instance – tests can monkeypatch this.
notifications = NotificationsService()


def alert_no_plan(user_id: int, day: str) -> None:
    """Send a reminder that ``day`` lacks any scheduled activities."""

    message = f"You have no plan for {day}."
    notifications.create(user_id, "Plan Reminder", message, type_="reminder")


def alert_pending_outcomes(user_id: int, day: str) -> None:
    """Notify that activities from ``day`` have not been processed."""

    message = f"Activities from {day} are awaiting processing."
    notifications.create(user_id, "Outcome Reminder", message, type_="reminder")


__all__ = [
    "Notification",
    "ScheduledEvent",
    "notifications",
    "alert_no_plan",
    "alert_pending_outcomes",
]

