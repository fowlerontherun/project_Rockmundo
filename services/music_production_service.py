from __future__ import annotations

"""Music production utilities influenced by avatar tech savvy."""

from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from services.avatar_service import AvatarService
from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from services.skill_service import skill_service


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
        user_id: int | None = None,
    ) -> dict[str, int]:
        """Return production metrics adjusted by tech_savvy and sound design skill.

        ``tech_savvy`` between 0-100 reduces time and stamina cost while
        increasing the XP gain from the session.  Values are clamped so the
        production still requires at least one minute and non-negative stamina.
        If ``user_id`` is provided, the user's ``sound_design`` skill further
        reduces production time and contributes a quality score.
        """

        avatar = self.avatar_service.get_avatar(band_id)
        tech = getattr(avatar, "tech_savvy", 0) if avatar else 0
        time_minutes = max(1, int(base_minutes * (100 - tech) / 100))
        stamina_cost = max(0, int(base_stamina_cost * (100 - tech) / 100))
        xp_gain = int(base_xp * (1 + tech / 100))


        # Factor in production-related skills
        prod = Skill(
            id=SKILL_NAME_TO_ID["music_production"],
            name="music_production",
            category="creative",
        )
        mixing = Skill(
            id=SKILL_NAME_TO_ID["mixing"],
            name="mixing",
            category="creative",
        )
        mastering = Skill(
            id=SKILL_NAME_TO_ID["mastering"],
            name="mastering",
            category="creative",
        )
        levels = [
            skill_service.train(band_id, prod, 0).level,
            skill_service.train(band_id, mixing, 0).level,
            skill_service.train(band_id, mastering, 0).level,
        ]
        avg_level = sum(levels) / len(levels)
        mult = 1 + avg_level / 200
        time_minutes = max(1, int(time_minutes / mult))
        xp_gain = int(xp_gain * mult)

        result = {
            "time_minutes": time_minutes,
            "stamina_cost": stamina_cost,
            "xp_gain": xp_gain,
        }

        if user_id is not None:
            skill = Skill(
                id=SKILL_NAME_TO_ID["sound_design"],
                name="sound_design",
                category="creative",
            )
            level = skill_service.train(user_id, skill, 0).level
            result["time_minutes"] = max(1, int(time_minutes * (100 - level * 5) / 100))
            result["quality"] = 1 + level * 0.1

        return result
