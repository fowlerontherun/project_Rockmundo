from __future__ import annotations

from models.admin import admin_sessions


class AdminMFAMiddleware:
    """Simple middleware-like helper enforcing MFA for /admin paths.

    This is a lightweight stand-in for Starlette's middleware system, suitable
    for the test environment where the full ASGI stack is not available.
    The ``dispatch`` method mirrors the interface of ``BaseHTTPMiddleware``.
    """

    async def dispatch(self, request, call_next):
        path = getattr(request, "path", "")
        if path.startswith("/admin") and not path.startswith("/admin/mfa"):
            session_id = request.headers.get("X-Admin-Session")
            session = admin_sessions.get(session_id or "")
            if not session or not session.verified or session.is_expired():
                raise PermissionError("MFA required")
        return await call_next(request)
