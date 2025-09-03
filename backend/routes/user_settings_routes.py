from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/user-settings", tags=["UserSettings"])

_USER_THEME: dict[int, str] = {}


class ThemePref(BaseModel):
  theme: str


@router.get("/theme/{user_id}")
def get_theme(user_id: int) -> dict[str, str]:
  return {"theme": _USER_THEME.get(user_id, "light")}


@router.post("/theme/{user_id}")
def set_theme(user_id: int, pref: ThemePref) -> dict[str, str]:
  _USER_THEME[user_id] = pref.theme
  return {"theme": pref.theme}
