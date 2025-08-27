from starlette.middleware.base import BaseHTTPMiddleware
from utils.i18n import set_locale, DEFAULT_LOCALE


class LocaleMiddleware(BaseHTTPMiddleware):
    """Middleware that sets the locale for each request."""

    async def dispatch(self, request, call_next):
        lang = request.headers.get("Accept-Language", DEFAULT_LOCALE)
        # take first language code before comma if multiple provided
        lang = lang.split(",")[0]
        set_locale(lang)
        response = await call_next(request)
        return response
