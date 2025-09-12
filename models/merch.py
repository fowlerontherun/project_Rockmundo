"""Dataclasses representing merchandise products and stock keeping units.

The project previously embedded simple dataclasses directly inside the
merch service.  They are now promoted to a dedicated module so that the
models can be reused by other parts of the application and in tests.

The ``ProductIn`` dataclass captures high level details about a
merchandise product such as its type and optional band association.  The
``SKUIn`` dataclass represents a concrete design/variant of a product
including its price and inventory level.  ``CartItem`` is used when
building orders.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductIn:
    """Input model for creating a merch product."""

    name: str
    category: str  # e.g. 'tshirt', 'poster', 'sticker'
    band_id: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True


@dataclass
class SKUIn:
    """Input model for creating a product variant/SKU."""

    product_id: int
    price_cents: int
    stock_qty: int
    option_size: Optional[str] = None
    option_color: Optional[str] = None
    currency: str = "USD"
    barcode: Optional[str] = None
    is_active: bool = True


@dataclass
class CartItem:
    """Represents an item placed in a user's cart for purchase."""

    sku_id: int
    qty: int


__all__ = ["ProductIn", "SKUIn", "CartItem"]

