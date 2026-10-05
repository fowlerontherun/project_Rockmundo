import sqlite3
from services.luthiery_catalogue_service import LuthieryCatalogueService

def test_admin_can_balance_unlock_price_and_supply(tmp_path):
 p=str(tmp_path/"cat.db");s=LuthieryCatalogueService(p);s.ensure_schema()
 out=s.admin_update("material","luthier.material.basswood",required_level=5,cost_cents=5000,stock=17)
 assert out["required_level"]==5 and out["cost_cents"]==5000
 with sqlite3.connect(p) as c:
  assert c.execute("SELECT required_level FROM crafting_unlocks WHERE content_key='luthier.material.basswood'").fetchone()[0]==5
  assert c.execute("SELECT quantity FROM luthier_supplier_stock WHERE material_id=(SELECT id FROM crafting_materials WHERE key='luthier.material.basswood')").fetchone()[0]==17
