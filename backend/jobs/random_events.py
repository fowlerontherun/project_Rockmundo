"""Scheduler job to trigger random events."""
from backend.services.random_event_service import random_event_service


def run() -> tuple[int, str]:
    count = random_event_service.run_scheduled_events()
    return count, "random_events_triggered"
