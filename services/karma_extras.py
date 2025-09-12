from datetime import datetime
from collections import defaultdict

# Simulated database
karma_scores = defaultdict(int)
karma_votes = defaultdict(list)
karma_leaderboard = []

def add_karma_vote(voter_id, target_id, vote_value):
    if vote_value not in [-1, 1]:
        raise ValueError("Vote must be -1 or 1")
    karma_scores[target_id] += vote_value
    karma_votes[target_id].append({'from': voter_id, 'value': vote_value, 'timestamp': datetime.utcnow()})
    return karma_scores[target_id]

def get_karma_score(user_id):
    return karma_scores.get(user_id, 0)

def get_karma_leaderboard():
    sorted_scores = sorted(karma_scores.items(), key=lambda x: x[1], reverse=True)
    return [{'user_id': uid, 'karma': score} for uid, score in sorted_scores[:10]]