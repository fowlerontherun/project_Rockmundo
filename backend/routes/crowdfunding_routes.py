from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.crowdfunding_service import CrowdfundingService, CrowdfundingError
from backend.services.economy_service import EconomyService

router = APIRouter(prefix="/crowdfunding", tags=["Crowdfunding"])
svc = CrowdfundingService(economy=EconomyService())
svc.ensure_schema()


class CampaignCreateIn(BaseModel):
    creator_id: int
    goal_cents: int
    creator_share: float = 0.8
    backer_share: float = 0.2


@router.post("/campaigns")
def launch_campaign(payload: CampaignCreateIn):
    cid = svc.create_campaign(
        creator_id=payload.creator_id,
        goal_cents=payload.goal_cents,
        creator_share=payload.creator_share,
        backer_share=payload.backer_share,
    )
    return {"campaign_id": cid}


class PledgeIn(BaseModel):
    campaign_id: int
    backer_id: int
    amount_cents: int


@router.post("/pledge")
def pledge(payload: PledgeIn):
    try:
        pid = svc.pledge(payload.campaign_id, payload.backer_id, payload.amount_cents)
        return {"pledge_id": pid}
    except CrowdfundingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # Economy errors
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/campaigns/{campaign_id}/complete")
def complete_campaign(campaign_id: int):
    try:
        svc.complete_campaign(campaign_id)
        return {"ok": True}
    except CrowdfundingError as e:
        raise HTTPException(status_code=400, detail=str(e))
