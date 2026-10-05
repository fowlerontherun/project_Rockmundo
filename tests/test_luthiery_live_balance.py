import sqlite3
import pytest
from services.luthiery_balance_service import LuthieryBalanceService

def test_quality_weights_are_validated_and_persist(tmp_path):
 s=LuthieryBalanceService(tmp_path/"b.db")
 v={"skill":.4,"materials":.3,"specialist":.15,"workshop":.1,"variance":.05}
 assert s.set_quality_weights(v)==v
 assert s.quality_weights()==v
 with pytest.raises(ValueError):s.set_quality_weights({**v,"skill":.5})

def test_trait_control_defaults_on_and_can_disable(tmp_path):
 s=LuthieryBalanceService(tmp_path/"b.db")
 assert s.trait_enabled("hot_pickups") is True
 s.set_trait("hot_pickups",False)
 assert s.trait_enabled("hot_pickups") is False
