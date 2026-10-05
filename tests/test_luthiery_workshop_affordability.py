from pathlib import Path

def test_workshop_response_includes_usd_affordability():
 source=Path("services/luthiery_workshop_service.py").read_text()
 assert "currency='USD'" in source
 assert 'out["balance_cents"]' in source
 assert 'out["can_afford_next_upgrade"]' in source

def test_workshop_ui_disables_unaffordable_upgrade():
 source=Path("frontend/src/crafting/LuthieryWorkshop.tsx").read_text()
 assert "Available funds:" in source
 assert "!workshop.can_afford_next_upgrade" in source
 assert "Insufficient funds" in source
