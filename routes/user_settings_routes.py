from fastapi import APIRouter
from pydantic import BaseModel

from backend.models import user_settings

router = APIRouter(prefix="/user-settings", tags=["UserSettings"])


class ThemePref(BaseModel):
    theme: str


class ProfilePref(BaseModel):
    bio: str = ""
    links: list[str] = []


@router.get("/theme/{user_id}")
def get_theme(user_id: int) -> dict[str, str]:
    return {"theme": user_settings.get_settings(user_id)["theme"]}


@router.post("/theme/{user_id}")
def set_theme(user_id: int, pref: ThemePref) -> dict[str, str]:
    settings = user_settings.get_settings(user_id)
    user_settings.set_settings(
        user_id,
        pref.theme,
        settings["bio"],
        settings["links"],
        settings["timezone"],
    )
    return {"theme": pref.theme}


@router.get("/profile/{user_id}")
def get_profile(user_id: int) -> dict:
    settings = user_settings.get_settings(user_id)
    return {"bio": settings["bio"], "links": settings["links"]}


@router.post("/profile/{user_id}")
def set_profile(user_id: int, pref: ProfilePref) -> dict:
    settings = user_settings.get_settings(user_id)
    user_settings.set_settings(
        user_id,
        settings["theme"],
        pref.bio,
        pref.links,
        settings["timezone"],
    )
    return {"bio": pref.bio, "links": pref.links}
