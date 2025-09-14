
# ruff: noqa: I001
import os
from pathlib import Path

from auth.dependencies import get_current_user_id
from auth.routes import admin_mfa_router
from core.config import settings
from database import init_db
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from middleware.admin_mfa import AdminMFAMiddleware
from middleware.locale import LocaleMiddleware
from middleware.observability import ObservabilityMiddleware
from middleware.rate_limit import RateLimitMiddleware
from routes import (
    admin_analytics_routes,
    admin_media_moderation_routes,
    admin_routes,
    apprenticeship_routes,
    avatar,
    band_routes,
    character,
    chemistry_routes,
    crafting_routes,
    daily_loop_routes,
    event_routes,
    gifting_routes,
    jobs_routes,
    legacy_routes,
    lifestyle_routes,
    locale_routes,
    mail_routes,
    media_routes,
    membership_routes,
    merch_routes,
    notifications_routes,
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
    live_album_routes,
    support_slot_routes,
    tour_collab_routes,
    tour_planner_routes,
    trade_routes,
    business_training_routes,
    image_training_routes,
    attribute_routes,
    perk_routes,
    university_routes,
    user_settings_routes,
    venue_sponsorships_routes,
    video_routes,
    world_pulse_routes,
    skin_marketplace,
    festival_proposals_routes,
    jam_ws,
    notifications_ws,
)
from utils import db as backend_db
from utils.i18n import _

from services.scheduler_service import schedule_daily_loop_reset
from services.storage_service import get_storage_backend
from storage.local import LocalStorage
from utils.error_handlers import http_exception_handler
from utils.logging import setup_logging
from utils.metrics import CONTENT_TYPE_LATEST, generate_latest
from utils.tracing import setup_tracing

app = FastAPI(title="RockMundo API with Events, Lifestyle, and Sponsorships")
app.add_exception_handler(HTTPException, http_exception_handler)
cors_kwargs = {
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.env == "dev":
    cors_kwargs["allow_origin_regex"] = r"http://localhost(:[0-9]+)?"
else:
    cors_kwargs["allow_origins"] = settings.cors.allowed_origins

app.add_middleware(CORSMiddleware, **cors_kwargs)
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
async def startup() -> None:
    '''Initialize logging, tracing and database connections.

    The tracing exporter can be selected with the ``TRACING_EXPORTER``
    environment variable. Supported values are ``console`` (default),
    ``otlp`` and ``jaeger``. Additional variables such as ``JAEGER_HOST``
    and ``JAEGER_PORT`` configure exporter specifics.
    '''

    setup_logging()
    exporter = os.getenv("TRACING_EXPORTER", "console")
    setup_tracing(exporter)
    init_db()
    await backend_db._init_pool_async()
    schedule_daily_loop_reset()
    storage = get_storage_backend()
    if isinstance(storage, LocalStorage):
        os.makedirs(os.path.join(storage.root, "mail", "attachments"), exist_ok=True)


# Existing routers
app.include_router(event_routes.router, prefix="/api/events", tags=["Events"])
app.include_router(lifestyle_routes.router, prefix="/api", tags=["Lifestyle"])
app.include_router(admin_routes.router)
app.include_router(
    admin_media_moderation_routes.router,
    prefix="/admin",
    tags=["Admin Media Moderation"],
)
app.include_router(
    admin_analytics_routes.router, prefix="/api", tags=["Admin Analytics"]
)
app.include_router(jobs_routes.router, prefix="/api", tags=["Admin Jobs"])
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
app.include_router(
    business_training_routes.router,
    prefix="/api/training/business",
    tags=["BusinessTraining"],
)
app.include_router(
    image_training_routes.router,
    prefix="/api/training/image",
    tags=["ImageTraining"],
)
app.include_router(
    attribute_routes.router,
    prefix="/api",
    tags=["Attributes"],
)
app.include_router(perk_routes.router, prefix="/api", tags=["Perks"])
app.include_router(university_routes.router, prefix="/api", tags=["University"])
app.include_router(daily_loop_routes.router, prefix="/api", tags=["DailyLoop"])
app.include_router(user_settings_routes.router, prefix="/api", tags=["UserSettings"])
app.include_router(live_album_routes.router, prefix="/api", tags=["LiveAlbums"])
app.include_router(avatar.router, prefix="/api", tags=["Avatars"])
app.include_router(character.router, prefix="/api", tags=["Characters"])
app.include_router(band_routes.router, prefix="/api", tags=["Bands"])
app.include_router(playlist_routes.router, prefix="/api", tags=["Playlists"])
app.include_router(chemistry_routes.router)
app.include_router(crafting_routes.router, prefix="/api", tags=["Crafting"])
app.include_router(gifting_routes.router, prefix="/api", tags=["Gifting"])
app.include_router(shipping_routes.router, prefix="/api", tags=["Shipping"])
app.include_router(trade_routes.router, prefix="/api", tags=["Trade"])
app.include_router(membership_routes.router, prefix="/api", tags=["Membership"])
app.include_router(merch_routes.router, prefix="/api", tags=["Merch"])
app.include_router(mail_routes.router, prefix="/api", tags=["Mail"])
app.include_router(
    notifications_routes.router,
    prefix="/api",
    tags=["Notifications"],
    dependencies=[Depends(get_current_user_id)],
)
app.include_router(skin_marketplace.router, prefix="/api", tags=["Skins"])
app.include_router(
    festival_proposals_routes.router,
    prefix="/api",
    tags=["Festival Proposals"],
)

# Optional realtime features
if settings.realtime.backend != "disabled":
    app.include_router(jam_ws.router)
    app.include_router(notifications_ws.router)



@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": _("Welcome to RockMundo API")}
