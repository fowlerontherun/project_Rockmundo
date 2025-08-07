from fastapi import APIRouter
from schemas.live_performance import LivePerformanceCreate, LivePerformanceResponse
from typing import List

router = APIRouter()

performances_db = []
performance_id_counter = 1

@router.post("/performances/", response_model=LivePerformanceResponse)
def create_performance(perf: LivePerformanceCreate):
    global performance_id_counter
    new_perf = perf.dict()
    new_perf.update({
        "id": performance_id_counter,
        "performance_score": 0.0,
        "crowd_engagement": 0.0,
        "fame_gain": 0.0,
        "skill_gain": 0.0,
        "revenue": 0.0
    })
    performances_db.append(new_perf)
    performance_id_counter += 1
    return new_perf

@router.get("/performances/", response_model=List[LivePerformanceResponse])
def list_performances():
    return performances_db