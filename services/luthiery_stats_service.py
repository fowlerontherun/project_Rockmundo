"""Phase 5 stat profiles, traits and gameplay effects for crafted instruments."""
from __future__ import annotations
import json

CHARACTERISTICS=("tone","sustain","clarity","output","playability","reliability","durability","stage_impact")
TRAIT_RULES=(
 ("exceptional_sustain","Exceptional Sustain","sustain",78,{"sustain":5},None),
 ("perfectly_balanced","Perfectly Balanced","playability",78,{"playability":4,"reliability":2},None),
 ("hot_pickups","Hot Pickups","output",76,{"output":5,"stage_impact":2},"rock"),
 ("studio_clean","Studio Clean","clarity",80,{"clarity":5,"tone":2},"pop"),
 ("road_warrior","Road Warrior","durability",80,{"durability":5,"reliability":3},None),
 ("vintage_character","Vintage Character","tone",82,{"tone":5,"sustain":2},"blues"),
 ("heavyweight","Heavyweight","sustain",72,{"sustain":3,"playability":-2},"metal"),
 ("temperamental_electronics","Temperamental Electronics","output",68,{"output":4,"reliability":-4},None),
)
CONFLICTS={frozenset(("road_warrior","temperamental_electronics")),frozenset(("perfectly_balanced","heavyweight"))}

def build_profile(resolved_parts, quality:float, skills:dict)->dict:
    stats={k:40.0+quality*.25 for k in CHARACTERISTICS}
    genres={}
    for part,material,component in resolved_parts:
        for source in (material,component):
            if not source: continue
            raw=source["stat_affinities_json"] if "stat_affinities_json" in source.keys() else "{}"
            for k,v in json.loads(raw or "{}").items():
                if k in stats: stats[k]+=float(v)*3
    specialist={
      "woodworking":("tone","durability"),"fretwork":("playability","sustain"),
      "instrument_electronics":("output","clarity"),"instrument_finishing":("stage_impact","reliability")}
    for skill,targets in specialist.items():
        bump=min(5,float(skills.get(skill,0))/20)
        for k in targets: stats[k]+=bump
    stats={k:round(max(1,min(100,v)),2) for k,v in stats.items()}
    traits=[]
    for key,name,driver,threshold,effects,genre in TRAIT_RULES:
        if stats[driver] < threshold: continue
        if any(frozenset((key,t["key"])) in CONFLICTS for t in traits): continue
        traits.append({"key":key,"name":name,"effects":effects})
        if genre: genres[genre]=round(min(0.05,(stats[driver]-65)/700),3)
        if len(traits)>=3: break
    for t in traits:
        for k,v in t["effects"].items(): stats[k]=round(max(1,min(100,stats[k]+v)),2)
    # Gameplay modifiers are derived from the final post-trait characteristics.
    mods={
      "performance_quality":round((stats["tone"]+stats["playability"])/2000,4),
      "instrument_effectiveness":round(sum(stats.values())/len(stats)/1800,4),
      "recording_quality":round((stats["clarity"]+stats["tone"])/2000,4),
      "practice_effectiveness":round(stats["playability"]/2200,4),
      "stage_presence":round(stats["stage_impact"]/1800,4),
      "audience_reaction":round((stats["stage_impact"]+stats["output"])/2400,4),
      "reliability":round((stats["reliability"]+stats["durability"])/2000,4),
    }
    return {"characteristics":stats,"traits":traits,"gameplay_modifiers":mods,"genre_affinities":genres}
