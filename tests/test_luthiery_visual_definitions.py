from services.luthiery_visual_definitions import SHAPES, PARTS, visual_definition, validate_combination

def test_all_shapes_have_complete_normalized_anchors():
    assert len(SHAPES)>=20
    for key,_name,_kind,_level,_asset in SHAPES:
        v=visual_definition(key)
        assert set(v["anchors"])==set(PARTS)
        for anchor in v["anchors"].values():
            assert 0<=anchor["x"]<=1 and 0<=anchor["y"]<=1
            assert anchor["scale"]>0

def test_starter_guitar_and_bass_shapes_present():
    keys={s[0] for s in SHAPES}
    for key in ("luthier.shape.guitar.s_style","luthier.shape.guitar.t_style",
                "luthier.shape.guitar.single_cut","luthier.shape.guitar.double_cut",
                "luthier.shape.bass.p_style","luthier.shape.bass.j_style"):
        assert key in keys

def test_combination_requires_exact_five_parts_and_correct_type():
    parts={p:{} for p in PARTS}
    assert validate_combination("luthier.shape.guitar.double_cut","guitar",parts)==[]
    assert "incompatible" in validate_combination("luthier.shape.guitar.double_cut","bass",parts)[0]
    assert validate_combination("luthier.shape.guitar.double_cut","guitar",{"body":{}})

def test_unknown_shape_has_safe_missing_asset_fallback():
    v=visual_definition("missing")
    assert v["missing"] is True and v["fallback"]=="generic_guitar"
