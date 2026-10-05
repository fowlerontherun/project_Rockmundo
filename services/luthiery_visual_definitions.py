"""Phase 3 visual shape definitions used by the workshop renderer."""
from __future__ import annotations

PARTS=("body","neck","fretboard","electronics","hardware")
def a(x,y,scale=1.0,rotation=0): return {"x":x,"y":y,"scale":scale,"rotation":rotation}

# Normalized 0..1 workshop canvas coordinates. These are deliberately renderer-agnostic.
BASE={
 "guitar":{"body":a(.50,.64,1),"neck":a(.50,.34,.92),"fretboard":a(.50,.36,.90),
           "electronics":a(.50,.61,.80),"hardware":a(.50,.72,.82)},
 "bass":{"body":a(.50,.66,1),"neck":a(.50,.31,1.05),"fretboard":a(.50,.34,1.02),
         "electronics":a(.50,.63,.82),"hardware":a(.50,.74,.85)}
}
SHAPES=(
 ("luthier.shape.guitar.double_cut","Double Cut","guitar",1,"double_cut"),
 ("luthier.shape.guitar.s_style","RockMundo S","guitar",10,"s_style"),
 ("luthier.shape.guitar.t_style","RockMundo T","guitar",20,"t_style"),
 ("luthier.shape.guitar.single_cut","Single Cut","guitar",40,"single_cut"),
 ("luthier.shape.bass.p_style","P-Style Bass","bass",1,"p_style"),
 ("luthier.shape.bass.j_style","J-Style Bass","bass",30,"j_style"),
 ("luthier.shape.guitar.v_style","V-Style","guitar",45,"v_style"),
 ("luthier.shape.guitar.explorer","Explorer-Style","guitar",50,"explorer"),
 ("luthier.shape.guitar.offset","Offset","guitar",55,"offset"),
 ("luthier.shape.guitar.modern_metal","Modern Metal","guitar",60,"modern_metal"),
 ("luthier.shape.guitar.headless","Headless","guitar",65,"headless"),
 ("luthier.shape.guitar.semi_hollow","Semi-Hollow","guitar",65,"semi_hollow"),
 ("luthier.shape.guitar.extended_range","Extended-Range Guitar","guitar",70,"extended_range"),
 ("luthier.shape.bass.extended_range","Extended-Range Bass","bass",70,"extended_range_bass"),
 ("luthier.shape.guitar.extreme_asymmetric","Extreme Asymmetric","guitar",80,"extreme_asymmetric"),
 ("luthier.shape.guitar.extreme_horns","Extreme Horns","guitar",85,"extreme_horns"),
 ("luthier.shape.guitar.coffin","RockMundo Coffin","guitar",90,"coffin"),
 ("luthier.shape.guitar.star","RockMundo Star","guitar",90,"star"),
 ("luthier.shape.guitar.extreme_v","Extreme V","guitar",95,"extreme_v"),
 ("luthier.shape.bass.signature_razor","RockMundo Razor Bass","bass",100,"signature_razor"),
)
VISUALS={key:{"asset_key":asset,"fallback":"generic_"+kind,"anchors":BASE[kind],
              "bounds":{"x":.12,"y":.08,"width":.76,"height":.86}}
         for key,_name,kind,_level,asset in SHAPES}

def visual_definition(shape_key:str)->dict:
    return VISUALS.get(shape_key,{"asset_key":"generic_guitar","fallback":"generic_guitar",
      "anchors":BASE["guitar"],"bounds":{"x":.12,"y":.08,"width":.76,"height":.86},"missing":True})

def validate_combination(shape_key:str,instrument_type:str,parts:dict)->list[str]:
    errors=[]
    row=next((s for s in SHAPES if s[0]==shape_key),None)
    if not row: return ["Unknown instrument shape"]
    if row[2]!=instrument_type: errors.append("Shape is incompatible with instrument type")
    missing=set(PARTS)-set(parts)
    extra=set(parts)-set(PARTS)
    if missing: errors.append("Missing parts: "+", ".join(sorted(missing)))
    if extra: errors.append("Unsupported parts: "+", ".join(sorted(extra)))
    return errors
