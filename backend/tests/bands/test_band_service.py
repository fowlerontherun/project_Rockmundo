from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.band_service import Base, BandMember, BandService


def get_service():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return BandService(SessionLocal), SessionLocal


def test_band_lifecycle_and_payouts():
    svc, SessionLocal = get_service()

    band = svc.create_band(user_id=1, band_name="AI Band", genre="rock")
    assert band.id is not None

    # founder automatically added; add two more members then remove one
    svc.add_member(band.id, 2, "drummer")
    svc.add_member(band.id, 3, "bassist")
    svc.remove_member(band.id, 2)

    info = svc.get_band_info(band.id)
    assert info and {m["user_id"] for m in info["members"]} == {1, 3}

    split = svc.split_earnings(band.id, 100)
    assert split["per_member"] == 50
    assert split["payouts"] == {1: 50, 3: 50}

    # verify membership persisted
    with SessionLocal() as session:
        members = session.query(BandMember).filter_by(band_id=band.id).all()
        assert len(members) == 2


def test_collaboration_split():
    svc, _ = get_service()
    band = svc.create_band(user_id=1, band_name="Band1", genre="rock")
    result = svc.split_earnings(band.id, 80, collaboration_band_id=2)
    assert result["band_1_share"] == 40
    assert result["band_2_share"] == 40

