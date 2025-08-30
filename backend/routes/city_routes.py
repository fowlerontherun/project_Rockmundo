"""API routes exposing city analytics."""
from fastapi import APIRouter, HTTPException

from backend.services.city_service import city_service

router = APIRouter(prefix="/cities", tags=["Cities"])


@router.get("/{name}")
def city_stats(name: str) -> dict:
    city = city_service.get_city(name)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city_service.stats(name)


@router.get("/popular")
def popular_cities(limit: int = 5) -> list[dict]:
    return city_service.popular_cities(limit)
