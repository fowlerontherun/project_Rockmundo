from fastapi import APIRouter
from schemas.election_schema import ElectionCreate, VoteCast
from models.election import Election
from datetime import datetime
from typing import List

router = APIRouter()
elections: List[Election] = []
election_id = 1

@router.post("/elections/", response_model=Election)
def create_election(data: ElectionCreate):
    global election_id
    new_election = Election(
        id=election_id,
        role=data.role,
        region=data.region,
        candidates=data.candidates,
        votes={cid: 0 for cid in data.candidates},
        open=True,
        start_date=data.start_date,
        end_date=data.end_date,
        campaign_promises=data.campaign_promises
    )
    elections.append(new_election)
    election_id += 1
    return new_election

@router.post("/elections/{eid}/vote")
def cast_vote(eid: int, vote: VoteCast):
    for election in elections:
        if election.id == eid and election.open:
            if vote.candidate_id in election.votes:
                election.votes[vote.candidate_id] += 1
            return {"status": "vote counted"}
    return {"error": "Election not found or closed"}

@router.get("/elections/", response_model=List[Election])
def list_elections():
    return elections