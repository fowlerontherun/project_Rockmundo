from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Ensure the default database path used by service exists during import
Path(__file__).resolve().parents[2].joinpath("database").mkdir(parents=True, exist_ok=True)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.avatar import Base as AvatarBase
from models.character import Base as CharacterBase, Character
from schemas.avatar import AvatarCreate
from services.avatar_service import AvatarService
from services.band_service import Base, BandMember, BandService
from services.band_relationship_service import BandRelationshipService
from services.skill_service import SkillService, SONGWRITING_SKILL


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


def test_relationship_modifier_affects_split():
    svc, _ = get_service()
    rel_svc = BandRelationshipService()
    svc.relationship_service = rel_svc
    band = svc.create_band(user_id=1, band_name="Band1", genre="rock")

    rel_svc.create_relationship(
        band_a_id=band.id,
        band_b_id=2,
        relationship_type="alliance",
        affinity=80,
        compatibility=90,
    )

    result = svc.split_earnings(band.id, 100, collaboration_band_id=2)
    expected_modifier = 1 + ((80 + 90) / 2 - 50) / 100
    expected_total = int(100 * expected_modifier)
    assert result["band_1_share"] + result["band_2_share"] == expected_total
    assert result["modifier"] == expected_modifier


def test_leadership_effects_on_training_and_decay():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    CharacterBase.metadata.create_all(bind=engine)
    AvatarBase.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    avatar_svc = AvatarService(SessionLocal)
    skill_svc = SkillService(avatar_service=avatar_svc)
    band_svc = BandService(SessionLocal, avatar_service=avatar_svc, skill_service=skill_svc)

    with SessionLocal() as session:
        chars = [
            Character(name=f"C{i}", genre="rock", trait="brave", birthplace="Earth")
            for i in range(4)
        ]
        session.add_all(chars)
        session.commit()
        ids = [c.id for c in chars]

    def make_avatar(cid, leadership):
        avatar_svc.create_avatar(
            AvatarCreate(
                character_id=cid,
                nickname=f"N{cid}",
                body_type="slim",
                skin_tone="pale",
                face_shape="oval",
                hair_style="short",
                hair_color="black",
                top_clothing="tshirt",
                bottom_clothing="jeans",
                shoes="boots",
                leadership=leadership,
            )
        )

    make_avatar(ids[0], 80)
    make_avatar(ids[1], 80)
    make_avatar(ids[2], 0)
    make_avatar(ids[3], 0)

    high_band = band_svc.create_band(user_id=ids[0], band_name="High", genre="rock")
    band_svc.add_member(high_band.id, ids[1])
    low_band = band_svc.create_band(user_id=ids[2], band_name="Low", genre="rock")
    band_svc.add_member(low_band.id, ids[3])

    for uid in ids:
        skill_svc.train(uid, SONGWRITING_SKILL, 0)

    band_svc.collective_training(high_band.id, SONGWRITING_SKILL, 10)
    band_svc.collective_training(low_band.id, SONGWRITING_SKILL, 10)

    xp_high = skill_svc._skills[(ids[0], SONGWRITING_SKILL.id)].xp
    xp_low = skill_svc._skills[(ids[2], SONGWRITING_SKILL.id)].xp
    assert xp_high > xp_low

    for uid in ids:
        skill_svc._skills[(uid, SONGWRITING_SKILL.id)].xp = 100

    band_svc.decay_band_skills(high_band.id, 10)
    band_svc.decay_band_skills(low_band.id, 10)

    after_high = skill_svc._skills[(ids[0], SONGWRITING_SKILL.id)].xp
    after_low = skill_svc._skills[(ids[2], SONGWRITING_SKILL.id)].xp
    assert 100 - after_high < 100 - after_low

