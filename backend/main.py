import os

from auth.routes import admin_mfa_router
from core.config import settings
from database import init_db
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from middleware.admin_mfa import AdminMFAMiddleware
from middleware.locale import LocaleMiddleware
from middleware.observability import ObservabilityMiddleware
from middleware.rate_limit import RateLimitMiddleware
from routes import (
    admin_routes,
    event_routes,
    legacy_routes,
    lifestyle_routes,
    locale_routes,
    social_routes,
    sponsorship,
    video_routes,
)
from utils.db import init_pool
from utils.i18n import _

from backend.utils.error_handlers import http_exception_handler
from backend.utils.logging import setup_logging
from backend.utils.metrics import CONTENT_TYPE_LATEST, generate_latest
from backend.utils.tracing import setup_tracing

app = FastAPI(title="RockMundo API with Events, Lifestyle, and Sponsorships")
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LocaleMiddleware)
app.add_middleware(AdminMFAMiddleware)


@app.on_event("startup")
def startup() -> None:
    """Initialize logging, tracing and database connections.

    The tracing exporter can be selected with the ``TRACING_EXPORTER``
    environment variable. Supported values are ``console`` (default),
    ``otlp`` and ``jaeger``. Additional variables such as ``JAEGER_HOST``
    and ``JAEGER_PORT`` configure exporter specifics.
    """

    setup_logging()
    exporter = os.getenv("TRACING_EXPORTER", "console")
    setup_tracing(exporter)
    init_db()
    init_pool()


# Existing routers
app.include_router(event_routes.router, prefix="/api/events", tags=["Events"])
app.include_router(lifestyle_routes.router, prefix="/api", tags=["Lifestyle"])
app.include_router(admin_routes.router, prefix="/admin", tags=["Admin"])
app.include_router(admin_mfa_router)

# Additional routers
app.include_router(sponsorship.router, prefix="/api/sponsorships", tags=["Sponsorships"])
app.include_router(social_routes.router, prefix="/api/social", tags=["Social"])
app.include_router(video_routes.router, tags=["Videos"])
app.include_router(legacy_routes.router, prefix="/api", tags=["Legacy"])
app.include_router(locale_routes.router, prefix="/api", tags=["Locale"])


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": _("Welcome to RockMundo API")}

