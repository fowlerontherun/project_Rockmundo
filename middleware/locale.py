from starlette.middleware.base import BaseHTTPMiddleware
from backend.utils.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, set_locale
from fastapi import Request
from typing import Callable

class LocaleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        locale = request.headers.get("Accept-Language", DEFAULT_LOCALE)
        if locale not in SUPPORTED_LOCALES:
            locale = DEFAULT_LOCALE
        set_locale(locale)
        response = await call_next(request)
        return response
