from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from .avatar import Base


class AvatarSkin(Base):
    """Association between an :class:`Avatar` and owned skins."""

    __tablename__ = "avatar_skins"

    id = Column(Integer, primary_key=True, index=True)
    avatar_id = Column(
        Integer,
        ForeignKey("avatars.id", use_alter=True, link_to_name=True),
        nullable=False,
    )
    skin_id = Column(Integer, nullable=False)
    is_applied = Column(Boolean, default=False)

    avatar = relationship("Avatar", back_populates="skins")
