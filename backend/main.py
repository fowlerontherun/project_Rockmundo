import os
from pathlib import Path

from auth.routes import admin_mfa_router
from core.config import settings
from database import init_db
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from middleware.admin_mfa import AdminMFAMiddleware
from middleware.locale import LocaleMiddleware
from middleware.observability import ObservabilityMiddleware
from middleware.rate_limit import RateLimitMiddleware
from routes import (
    admin_routes,
    apprenticeship_routes,
    avatar,
    character,
    chemistry_routes,
    crafting_routes,
    daily_loop_routes,
    event_routes,
    legacy_routes,
    lifestyle_routes,
    locale_routes,
    media_routes,
    membership_routes,
    mail_routes,
    music_metrics_routes,
    onboarding_routes,
    playlist_routes,
    sales,
    schedule_routes,
    setlist_routes,
    shipping_routes,
    social_routes,
    song_forecast_routes,
    sponsorship,
    support_slot_routes,
    tour_collab_routes,
    tour_planner_routes,
    trade_routes,
    university_routes,
    user_settings_routes,
    venue_sponsorships_routes,
    video_routes,
    world_pulse_routes,
)
from utils.db import init_pool
from utils.i18n import _

from backend.services.scheduler_service import schedule_daily_loop_reset
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

# Serve the frontend HTML pages from ``frontend/pages`` for local development.
frontend_pages = (
    Path(__file__).resolve().parent.parent / "frontend" / "pages"
)
if frontend_pages.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_pages), html=True), name="frontend")


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
    schedule_daily_loop_reset()


# Existing routers
app.include_router(event_routes.router, prefix="/api/events", tags=["Events"])
app.include_router(lifestyle_routes.router, prefix="/api", tags=["Lifestyle"])
app.include_router(admin_routes.router, prefix="/admin", tags=["Admin"])
app.include_router(admin_mfa_router)
app.include_router(apprenticeship_routes.router, prefix="/api", tags=["Apprenticeships"])

# Additional routers
app.include_router(sponsorship.router, prefix="/api/sponsorships", tags=["Sponsorships"])
app.include_router(venue_sponsorships_routes.router, prefix="/api", tags=["Venue Sponsorships"])
app.include_router(
    support_slot_routes.router,
    prefix="/api/support-slots",
    tags=["Support Slots"],
)
app.include_router(sales.router, prefix="/api", tags=["Sales"])
app.include_router(social_routes.router, prefix="/api/social", tags=["Social"])
app.include_router(media_routes.router, prefix="/api", tags=["Media & Publicity"])
app.include_router(video_routes.router, tags=["Videos"])
app.include_router(legacy_routes.router, prefix="/api", tags=["Legacy"])
app.include_router(locale_routes.router, prefix="/api", tags=["Locale"])
app.include_router(
    onboarding_routes.router,
    prefix="/api/onboarding",
    tags=["Onboarding"],
)
app.include_router(setlist_routes.router, prefix="/api", tags=["Setlists"])
app.include_router(music_metrics_routes.router)
app.include_router(world_pulse_routes.router, prefix="/api", tags=["World Pulse"])
app.include_router(schedule_routes.router, prefix="/api", tags=["Schedule"])
app.include_router(song_forecast_routes.router)
app.include_router(tour_collab_routes.router, prefix="/api", tags=["TourCollab"])
app.include_router(tour_planner_routes.router, prefix="/api", tags=["TourPlanner"])
app.include_router(university_routes.router, prefix="/api", tags=["University"])
app.include_router(daily_loop_routes.router, prefix="/api", tags=["DailyLoop"])
app.include_router(user_settings_routes.router, prefix="/api", tags=["UserSettings"])
app.include_router(avatar.router, prefix="/api", tags=["Avatars"])
app.include_router(character.router, prefix="/api", tags=["Characters"])
app.include_router(playlist_routes.router, prefix="/api", tags=["Playlists"])
app.include_router(chemistry_routes.router)
app.include_router(crafting_routes.router, prefix="/api", tags=["Crafting"])
app.include_router(shipping_routes.router, prefix="/api", tags=["Shipping"])
app.include_router(trade_routes.router, prefix="/api", tags=["Trade"])
app.include_router(membership_routes.router, prefix="/api", tags=["Membership"])
app.include_router(mail_routes.router, prefix="/api", tags=["Mail"])



@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": _("Welcome to RockMundo API")}

