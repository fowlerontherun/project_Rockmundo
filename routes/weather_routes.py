from backend.models.weather import Forecast
from services.weather_service import weather_service
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


@router.get("/weather/{region}", response_model=Forecast)
def get_forecast(region: str) -> Forecast:
    return weather_service.get_forecast(region)


class SubscribeRequest(BaseModel):
    region: str
    user_id: int


@router.post("/weather/subscribe")
def subscribe(req: SubscribeRequest) -> dict:
    weather_service.subscribe(req.region, req.user_id)
    return {"message": "subscribed"}
