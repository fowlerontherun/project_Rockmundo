import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.services.chemistry_service import ChemistryService, Base


def _service():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return ChemistryService(SessionLocal)


def test_pair_initialization_with_seeded_rng():
    svc = _service()
    random.seed(0)
    assert svc.initialize_pair(1, 2).score == 50
    random.seed(31)
    high = svc.initialize_pair(3, 4).score
    assert 81 <= high <= 100
    random.seed(2)
    low = svc.initialize_pair(5, 6).score
    assert 0 <= low <= 19


def test_adjust_pair_increases_score():
    svc = _service()
    pair = svc.initialize_pair(1, 2)
    start = pair.score
    pair = svc.adjust_pair(1, 2, 1)
    pair = svc.adjust_pair(1, 2, 2)
    assert pair.score == start + 3
