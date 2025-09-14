"""Scheduler job for daily lifestyle decay and XP rewards."""

from services.lifestyle_scheduler import apply_lifestyle_decay_and_xp_effects


def run() -> tuple[int, str]:
    """Apply lifestyle decay and grant daily XP for all users."""
    count = apply_lifestyle_decay_and_xp_effects()
    return count, "lifestyle_xp_awarded"
