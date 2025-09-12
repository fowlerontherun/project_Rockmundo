from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from models.skin import Skin, SkinInventory
from schemas.skin import SkinCreate, SkinResponse, SkinEquipRequest, SkinInventoryItem
from database import get_db
from utils.i18n import _

router = APIRouter(prefix="/skins", tags=["Skins"])

@router.post("/", response_model=SkinResponse, dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))])
def submit_skin(skin: SkinCreate, db: Session = Depends(get_db)):
    new_skin = Skin(**skin.dict())
    db.add(new_skin)
    db.commit()
    db.refresh(new_skin)
    return new_skin

@router.get("/", response_model=list[SkinResponse])
def list_all_skins(db: Session = Depends(get_db)):
    return db.query(Skin).filter(Skin.is_approved == True).all()

@router.put("/{skin_id}/approve", response_model=SkinResponse)
def approve_skin(skin_id: int, db: Session = Depends(get_db)):
    skin = db.query(Skin).get(skin_id)
    if not skin:
        raise HTTPException(status_code=404, detail=_("Skin not found"))
    skin.is_approved = True
    db.commit()
    db.refresh(skin)
    return skin

@router.post("/equip")
def equip_skin(req: SkinEquipRequest, db: Session = Depends(get_db)):
    # Unequip current skin in same slot
    db.query(SkinInventory).filter_by(character_id=req.character_id, slot=req.slot).update({"is_equipped": False})
    db.commit()

    # Check if owned
    inv = db.query(SkinInventory).filter_by(character_id=req.character_id, skin_id=req.skin_id).first()
    if not inv:
        raise HTTPException(status_code=400, detail=_("Skin not owned"))

    # Equip it
    inv.is_equipped = True
    inv.slot = req.slot
    db.commit()
    db.refresh(inv)
    return {"message": _("Skin equipped"), "slot": inv.slot}

@router.get("/inventory/{character_id}", response_model=list[SkinInventoryItem])
def get_inventory(character_id: int, db: Session = Depends(get_db)):
    inv = (
        db.query(SkinInventory)
        .options(joinedload(SkinInventory.skin))
        .filter_by(character_id=character_id)
        .all()
    )
    return [
        SkinInventoryItem(
            skin=i.skin,
            is_equipped=i.is_equipped,
            slot=i.slot,
            equipped_at=i.equipped_at
        )
        for i in inv
    ]
