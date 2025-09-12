from pydantic import BaseModel

class LabelSchema(BaseModel):
    name: str
    genre_focus: str
    max_roster: int
    reputation: float
    npc_owned: bool = True

class ManagementContractSchema(BaseModel):
    manager_id: int
    band_id: int
    cut_percentage: float
    perks: str
    active: bool = True

class LabelContractSchema(BaseModel):
    label_id: int
    band_id: int
    revenue_split: str
    advance_payment: float
    min_releases: int
    active: bool = True
