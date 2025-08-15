from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.avatar import Avatar
from schemas.avatar import AvatarCreate, AvatarResponse
from database import get_db

router = APIRouter(prefix="/avatars", tags=["Avatars"])

@router.post("/", response_model=AvatarResponse, dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))])
def create_avatar(avatar: AvatarCreate, db: Session = Depends(get_db)):
    existing = db.query(Avatar).filter_by(character_id=avatar.character_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Avatar already exists for this character")
    
    new_avatar = Avatar(**avatar.dict())
    db.add(new_avatar)
    db.commit()
    db.refresh(new_avatar)
    return new_avatar

@router.get("/{character_id}", response_model=AvatarResponse)
def get_avatar(character_id: int, db: Session = Depends(get_db)):
    avatar = db.query(Avatar).filter_by(character_id=character_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar

@router.put("/{character_id}", response_model=AvatarResponse)
def update_avatar(character_id: int, updated: AvatarCreate, db: Session = Depends(get_db)):
    avatar = db.query(Avatar).filter_by(character_id=character_id).first()
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    for key, value in updated.dict().items():
        setattr(avatar, key, value)

    db.commit()
    db.refresh(avatar)
    return avatar
