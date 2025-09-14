"""Clear expired event effects from the database."""

from services.event_service import clear_expired_events


def run() -> tuple[int, str]:
    deleted = clear_expired_events()
    return deleted, "expired_cleared"
