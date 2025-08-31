from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class LabelCreateSchema(BaseModel):
    name: str
    owner_id: Optional[int]
    is_npc: Optional[bool] = True


class RoyaltyTierSchema(BaseModel):
    threshold_units: int
    rate: float


class RecordContractSchema(BaseModel):
    advance_cents: int
    royalty_tiers: List[RoyaltyTierSchema] = Field(default_factory=list)
    term_months: int
    territory: str
    recoupable_budgets_cents: int = 0
    options: List[str] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)


class OfferRequestSchema(BaseModel):
    label_id: int
    band_id: int
    terms: RecordContractSchema


class CounterOfferSchema(BaseModel):
    terms: RecordContractSchema


class NegotiationSchema(BaseModel):
    id: int
    label_id: int
    band_id: int
    stage: str
    recoupable_cents: int
    recouped_cents: int
    terms: RecordContractSchema

    class Config:
        orm_mode = True
