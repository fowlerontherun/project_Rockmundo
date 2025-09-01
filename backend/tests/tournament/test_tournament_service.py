import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

sys_path = Path(__file__).resolve().parents[3]
import sys
if str(sys_path) not in sys.path:
    sys.path.append(str(sys_path))

from backend.services.tournament_service import TournamentService


class DummyPerformance:
    def __init__(self, scores):
        self.scores = scores

    def simulate_gig(self, band_id, city, venue, setlist_revision_id=None, **_):
        value = self.scores[band_id]
        return {
            "status": "ok",
            "city": city,
            "venue": venue,
            "crowd_size": value * 10,
            "fame_earned": value,
            "revenue_earned": 0,
            "skill_gain": 0,
            "merch_sold": 0,
        }


def setup_service(scores):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE bands (id INTEGER PRIMARY KEY, revenue INTEGER)")
    for i in range(1, 5):
        cur.execute("INSERT INTO bands (id, revenue) VALUES (?, 0)", (i,))
    conn.commit()
    conn.close()
    perf = DummyPerformance(scores)
    svc = TournamentService(performance_service=perf, db_path=path, prize_amount=1000)
    return svc, path


def test_bracket_progression_and_prize():
    scores = {1: 10, 2: 20, 3: 5, 4: 15}
    svc, db_path = setup_service(scores)
    tid = svc.create_tournament([1, 2, 3, 4])
    bracket = svc.get_bracket(tid)
    assert len(bracket.rounds[0]) == 2

    champion = svc.play_round(bracket)
    assert champion is None
    assert len(bracket.rounds) == 2
    assert [m.winner_id for m in bracket.rounds[0]] == [2, 4]

    champion = svc.play_round(bracket)
    assert champion == 2

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT revenue FROM bands WHERE id = 2")
    winner_revenue = cur.fetchone()[0]
    cur.execute("SELECT revenue FROM bands WHERE id = 1")
    loser_revenue = cur.fetchone()[0]
    conn.close()

    assert winner_revenue == 2000
    assert loser_revenue == 0
