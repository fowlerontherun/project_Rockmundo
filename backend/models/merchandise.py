from pydantic import BaseModel
from typing import Optional
from datetime import date

class Merchandise(BaseModel):
    id: int
    band_id: int
    name: str
    category: str  # 'apparel', 'music', 'accessory', 'specialty'
    design_theme: Optional[str]
    base_cost: float
    sale_price: float
    quantity_available: int
    quantity_sold: int
    fame_boost_on_sale: float
    release_date: date
    sales_channel: str  # 'gig', 'tour', 'online'
    limited_edition: bool
    # Added cost breakdown
    production_cost: float
    packaging_cost: float
    shipping_cost: float
    sales_staff_cost: float
    storage_cost: Optional[float]