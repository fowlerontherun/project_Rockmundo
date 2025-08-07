candidates = []
votes = []

def declare_candidate(payload):
    candidates.append(payload)
    return {"status": "declared", "candidate": payload}

def vote_for_candidate(payload):
    votes.append(payload)
    return {"status": "vote_cast", "vote": payload}

def get_election_results():
    tally = {}
    for vote in votes:
        cid = vote["candidate_id"]
        tally[cid] = tally.get(cid, 0) + 1
    results = [{"candidate_id": k, "votes": v} for k, v in sorted(tally.items(), key=lambda x: x[1], reverse=True)]
    return {"results": results}