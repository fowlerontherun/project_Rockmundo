"""Admin routes for managing drug items and categories."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_permission
from backend.models.item import Item, ItemCategory
from backend.models.drug import Drug
from backend.services.admin_audit_service import audit_dependency
from backend.services.item_service import ItemService

router = APIRouter(tags=["AdminDrugs"], dependencies=[Depends(audit_dependency)])
svc = ItemService()


class DrugCategoryIn(BaseModel):
    name: str
    description: str = ""


class DrugIn(BaseModel):
    name: str
    category: str
    effects: list[str] = []
    addiction_rate: float = 0.0
    duration: int = 0
    price_cents: int = 0
    stock: int = 0


def _item_to_drug(item: Item) -> Drug:
    return Drug(
        id=item.id,
        name=item.name,
        category=item.category,
        stats=item.stats,
        price_cents=item.price_cents,
        stock=item.stock,
        effects=item.stats.get("effects", []),
        addiction_rate=item.stats.get("addiction_rate", 0.0),
        duration=item.stats.get("duration", 0),
    )


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


# ---------------------------------------------------------------------------
# Category routes
# ---------------------------------------------------------------------------


@router.get("/drug-categories")
async def list_drug_categories(req: Request) -> list[ItemCategory]:
    await _ensure_admin(req)
    return svc.list_categories()


@router.post("/drug-categories")
async def create_drug_category(payload: DrugCategoryIn, req: Request) -> ItemCategory:
    await _ensure_admin(req)
    category = ItemCategory(**payload.model_dump())
    return svc.create_category(category)


@router.put("/drug-categories/{name}")
async def update_drug_category(name: str, payload: DrugCategoryIn, req: Request) -> ItemCategory:
    await _ensure_admin(req)
    category = ItemCategory(name=name, description=payload.description)
    return svc.create_category(category)


@router.delete("/drug-categories/{name}")
async def delete_drug_category(name: str, req: Request) -> dict[str, str]:
    await _ensure_admin(req)
    svc.delete_category(name)
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Drug item routes
# ---------------------------------------------------------------------------


@router.get("/drugs")
async def list_drugs(req: Request) -> list[Drug]:
    await _ensure_admin(req)
    items = svc.list_items()
    return [_item_to_drug(i) for i in items if "effects" in i.stats]


@router.post("/drugs")
async def create_drug(payload: DrugIn, req: Request) -> Drug:
    await _ensure_admin(req)
    drug = Drug(id=None, **payload.model_dump())
    return svc.create_item(drug)  # type: ignore[return-value]


@router.get("/drugs/{drug_id}")
async def get_drug(drug_id: int, req: Request) -> Drug:
    await _ensure_admin(req)
    try:
        item = svc.get_item(drug_id)
    except ValueError as exc:  # pragma: no cover - handled via HTTPException
        raise HTTPException(status_code=404, detail=str(exc))
    return _item_to_drug(item)


@router.put("/drugs/{drug_id}")
async def update_drug(drug_id: int, payload: DrugIn, req: Request) -> Drug:
    await _ensure_admin(req)
    stats = {
        "effects": payload.effects,
        "addiction_rate": payload.addiction_rate,
        "duration": payload.duration,
    }
    try:
        item = svc.update_item(
            drug_id,
            name=payload.name,
            category=payload.category,
            stats=stats,
            price_cents=payload.price_cents,
            stock=payload.stock,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _item_to_drug(item)


@router.delete("/drugs/{drug_id}")
async def delete_drug(drug_id: int, req: Request) -> dict[str, str]:
    await _ensure_admin(req)
    svc.delete_item(drug_id)
    return {"status": "deleted"}

