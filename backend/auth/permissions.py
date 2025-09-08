from enum import Enum

class Permissions(str, Enum):
    """Canonical permission strings used throughout the application."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    BAND_MEMBER = "band_member"
    USER = "user"
    PLAYER = "player"
