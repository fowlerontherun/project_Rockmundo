from pathlib import Path
import ast

def test_live_and_preview_normalize_crafting_inputs():
 source=Path("services/luthiery_crafting_service.py").read_text();ast.parse(source)
 assert "\\nfrom services" not in source
 assert source.count("skills,workshop_score=self._normalize_inputs(skills,workshop_score)")>=2
 for key in ("luthiery","woodworking","fretwork","instrument_electronics","instrument_finishing"):
  assert f'"{key}"' in source
 assert "skill must be between 0 and 100" in source
 assert "Workshop score must be between 0 and 100" in source

def test_normalized_values_feed_profile_and_snapshots():
 source=Path("services/luthiery_crafting_service.py").read_text()
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 assert "build_profile(resolved, score, skills)" in craft
 assert 'json.dumps(skills, sort_keys=True)' in craft
 assert 'json.dumps({"score": workshop_score' in craft
