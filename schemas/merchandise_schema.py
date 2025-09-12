from pydantic import BaseModel
from typing import Optional
from datetime import date

class MerchandiseCreate(BaseModel):
    band_id: int
    name: str
    category: str
    design_theme: Optional[str]
    base_cost: float
    sale_price: float
    quantity_available: int
    release_date: date
    sales_channel: str
    limited_edition: bool
    production_cost: float
    packaging_cost: float
    shipping_cost: float
    sales_staff_cost: float
    storage_cost: Optional[float]

class MerchandiseResponse(MerchandiseCreate):
    id: int
    quantity_sold: int
    fame_boost_on_sale: float