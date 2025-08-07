from typing import List
from datetime import datetime, timedelta
from collections import defaultdict

class FanTourVote:
    def __init__(self, band_id: int, city: str, fan_id: int):
        self.band_id = band_id
        self.city = city
        self.fan_id = fan_id
        self.vote_time = datetime.utcnow()

class CityPetition:
    def __init__(self, band_id: int, city: str):
        self.city = city
        self.band_id = band_id
        self.total_votes = 0
        self.status = "pending"
        self.created_at = datetime.utcnow()

class FanEngagementEffect:
    def __init__(self, band_id: int, city: str, fame_bonus: float, karma_bonus: float):
        self.band_id = band_id
        self.city = city
        self.fame_bonus = fame_bonus
        self.karma_bonus = karma_bonus
        self.triggered_on = datetime.utcnow()

votes: List[FanTourVote] = []
petitions: dict = {}
bonuses: List[FanEngagementEffect] = []
VOTE_COOLDOWN = timedelta(hours=24)

def cast_vote(band_id: int, city: str, fan_id: int):
    now = datetime.utcnow()
    recent = [v for v in votes if v.fan_id == fan_id and v.band_id == band_id and now - v.vote_time < VOTE_COOLDOWN]
    if recent:
        return {"status": "error", "reason": "Cooldown in effect"}

    vote = FanTourVote(band_id, city, fan_id)
    votes.append(vote)

    key = f"{band_id}:{city.lower()}"
    if key not in petitions:
        petitions[key] = CityPetition(band_id, city)
    petitions[key].total_votes += 1

    if petitions[key].total_votes >= 100:
        petitions[key].status = "qualified"

    return {"status": "success", "vote": vote.__dict__, "petition": petitions[key].__dict__}

def get_votes_for_band(band_id: int):
    filtered = [v for v in votes if v.band_id == band_id]
    return [v.__dict__ for v in filtered]

def get_top_petitions(band_id: int):
    band_petitions = [p for k, p in petitions.items() if p.band_id == band_id]
    sorted_petitions = sorted(band_petitions, key=lambda p: p.total_votes, reverse=True)
    return [p.__dict__ for p in sorted_petitions]

def trigger_engagement_bonus(band_id: int, city: str):
    bonus = FanEngagementEffect(band_id, city, fame_bonus=2.0, karma_bonus=1.5)
    bonuses.append(bonus)
    return bonus.__dict__