from fastapi import APIRouter
from utils.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES

router = APIRouter()


@router.get("/locales")
def get_locales() -> dict[str, list[str] | str]:
    """Expose supported locales and the default fallback."""
    return {"default": DEFAULT_LOCALE, "locales": SUPPORTED_LOCALES}
