from pathlib import Path
from services.luthiery_balance_service import LuthieryBalanceService

def test_advanced_features_default_off_and_persist(tmp_path):
 s=LuthieryBalanceService(tmp_path/"b.db")
 assert s.feature_enabled("legendary_shapes") is False
 assert s.set_feature("legendary_shapes",True)["enabled"] is True
 assert s.feature_enabled("legendary_shapes") is True

def test_admin_luthiery_source_has_no_literal_newline_escape_regression():
 source=Path("routes/admin_luthiery_routes.py").read_text()
 assert "luthiery_reputation\\\\nfrom" not in source
 assert "class QualityWeightsUpdate(BaseModel):\\\\n" not in source
