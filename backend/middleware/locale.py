from starlette.middleware.base import BaseHTTPMiddleware
from utils.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, set_locale


class LocaleMiddleware(BaseHTTPMiddleware):
    """Middleware that sets the locale for each request."""

    async def dispatch(self, request, call_next):
        candidates: list[str] = []

        # query string has highest priority
        q = request.query_params.get("lang")
        if q:
            candidates.append(q)

        # cookie next
        cookie_lang = request.cookies.get("lang")
        if cookie_lang:
            candidates.append(cookie_lang)

        # Accept-Language header may list multiple values with quality params
        header = request.headers.get("Accept-Language", "")
        for part in header.split(","):
            code = part.split(";")[0].strip()
            if code:
                candidates.append(code)
                base = code.split("-")[0]
                if base and base != code:
                    candidates.append(base)

        # finally fall back to default locale
        candidates.append(DEFAULT_LOCALE)

        for lang in candidates:
            if lang in SUPPORTED_LOCALES:
                set_locale(lang)
                break

        response = await call_next(request)
        return response
