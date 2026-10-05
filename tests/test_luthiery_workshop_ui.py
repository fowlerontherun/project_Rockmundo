from pathlib import Path

def test_player_workshop_ui_loads_and_upgrades_server_workshop():
 source=Path("frontend/src/crafting/LuthieryWorkshop.tsx").read_text()
 assert "apiFetch('/luthiery/workshop')" in source
 assert "apiFetch('/luthiery/workshop/upgrade',{method:'POST'})" in source
 assert "Workshop quality {workshop.quality_score}/100" in source
 assert "Upgrade level {workshop.upgrade_level}/5" in source
 assert "Maximum workshop quality" in source
 assert "contributes 10% of the instrument quality calculation" in source
