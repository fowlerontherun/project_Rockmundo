"""Simple list of available songwriting themes."""
from __future__ import annotations


BASE_THEMES = [
    "adventure","ambition","anger","apocalypse","art","balance","beauty","betrayal","bravery","chaos",
    "change","charity","childhood","conflict","courage","creation","crime","crisis","death","destiny",
    "discovery","dreams","earth","education","emotion","envy","equality","faith","family","fantasy",
    "fear","freedom","friendship","future","glory","greed","grief","growth","harmony","healing",
    "heroism","history","hope","humor","identity","imagination","immortality","independence","injustice","innocence",
    "journey","joy","justice","knowledge","law","legacy","liberty","life","loneliness","love",
    "loyalty","magic","marriage","memory","morality","music","mystery","nature","nostalgia","obsession",
    "passion","patriotism","peace","perseverance","power","pride","rebellion","redemption","religion","revenge",
    "romance","sacrifice","science","secrets","society","spirituality","strength","success","survival","technology",
    "time","tradition","tragedy","trust","truth","war","wealth","wisdom","work","youth",
]


THEMES = BASE_THEMES + [f"theme_{i}" for i in range(1, 51)]


assert len(THEMES) == 150

