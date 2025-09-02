from pydantic import BaseModel


class WorkshopSchema(BaseModel):
    id: int
    skill_target: str
    xp_reward: int
    ticket_price: int
    schedule: str


class WorkshopCreateSchema(BaseModel):
    skill_target: str
    xp_reward: int
    ticket_price: int
    schedule: str


__all__ = ["WorkshopSchema", "WorkshopCreateSchema"]
