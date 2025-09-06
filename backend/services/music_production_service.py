from __future__ import annotations

"""Music production utilities influenced by avatar tech savvy."""

from backend.services.avatar_service import AvatarService


class MusicProductionService:
    """Simplified production calculations that factor in an avatar's tech skills."""

    def __init__(self, avatar_service: AvatarService | None = None):
        self.avatar_service = avatar_service or AvatarService()

    def produce_track(
        self,
        band_id: int,
        base_minutes: int,
        base_stamina_cost: int = 10,
        base_xp: int = 5,
    ) -> dict[str, int]:
        """Return production metrics adjusted by tech_savvy.

        ``tech_savvy`` between 0-100 reduces time and stamina cost while
        increasing the XP gain from the session.  Values are clamped so the
        production still requires at least one minute and non-negative stamina.
        """

        avatar = self.avatar_service.get_avatar(band_id)
        tech = getattr(avatar, "tech_savvy", 0) if avatar else 0
        time_minutes = max(1, int(base_minutes * (100 - tech) / 100))
        stamina_cost = max(0, int(base_stamina_cost * (100 - tech) / 100))
        xp_gain = int(base_xp * (1 + tech / 100))
        return {
            "time_minutes": time_minutes,
            "stamina_cost": stamina_cost,
            "xp_gain": xp_gain,
        }
