import json
from services.luthiery_stats_service import build_profile, CHARACTERISTICS

class Row(dict):
    def keys(self): return super().keys()

def part(aff):
    return ("body",Row(stat_affinities_json=json.dumps(aff)),None)

def test_profile_has_all_characteristics_and_bounded_modifiers():
    p=build_profile([part({"tone":3,"sustain":2})],80,{"woodworking":80})
    assert set(p["characteristics"])==set(CHARACTERISTICS)
    assert all(1<=v<=100 for v in p["characteristics"].values())
    assert all(0<=v<=0.2 for v in p["gameplay_modifiers"].values())

def test_material_choices_create_different_profiles():
    tone=build_profile([part({"tone":4})],70,{})
    stage=build_profile([part({"stage_impact":4})],70,{})
    assert tone["characteristics"]["tone"]>stage["characteristics"]["tone"]
    assert stage["characteristics"]["stage_impact"]>tone["characteristics"]["stage_impact"]

def test_traits_do_not_conflict():
    p=build_profile([part({"durability":20,"output":20,"playability":20,"sustain":20})],100,{})
    keys={t["key"] for t in p["traits"]}
    assert not ({"road_warrior","temperamental_electronics"} <= keys)
    assert not ({"perfectly_balanced","heavyweight"} <= keys)

def test_genre_affinity_is_small_bonus_not_dominant():
    p=build_profile([part({"output":20})],100,{})
    assert all(0<=v<=0.05 for v in p["genre_affinities"].values())
