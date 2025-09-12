from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Skin(Base):
    __tablename__ = "skins"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)  # e.g. top, guitar, shoes, hair, etc.
    mesh_url = Column(String)
    texture_url = Column(String)
    rarity = Column(String)  # Common, Rare, Epic, Legendary
    author = Column(String)
    is_approved = Column(Boolean, default=False)
    is_official = Column(Boolean, default=False)
    price = Column(Integer, default=0)  # in-game currency or token cost
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SkinInventory(Base):
    __tablename__ = "skin_inventory"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    skin_id = Column(Integer, ForeignKey("skins.id"))
    is_equipped = Column(Boolean, default=False)
    slot = Column(String)  # where it's equipped (top, bottom, guitar, etc.)
    equipped_at = Column(DateTime(timezone=True), server_default=func.now())
