
from models.election import Election
from models.community_role import CommunityRole
from datetime import datetime, timedelta

class ElectionService:
    def __init__(self, db):
        self.db = db

    def create_election(self, role_name, candidates, duration_days=3):
        election = Election(
            id=None,
            role_name=role_name,
            candidates=candidates,
            votes={cid: 0 for cid in candidates},
            status="open",
            ends_at=(datetime.utcnow() + timedelta(days=duration_days)).isoformat()
        )
        self.db.insert_election(election)
        return election.to_dict()

    def vote(self, election_id, candidate_id):
        self.db.increment_vote(election_id, candidate_id)
        return {"status": "vote recorded"}

    def close_election(self, election_id):
        election = self.db.get_election(election_id)
        winner = max(election["votes"], key=election["votes"].get)
        role = CommunityRole(
            id=None,
            role_name=election["role_name"],
            holder_id=winner,
            type="npc" if str(winner).startswith("npc_") else "player"
        )
        self.db.assign_community_role(role)
        self.db.update_election_status(election_id, "closed")
        return {"winner": winner}
