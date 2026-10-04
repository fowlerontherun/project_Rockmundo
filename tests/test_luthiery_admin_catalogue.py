import sqlite3
import pytest
from services.luthiery_catalogue_service import LuthieryCatalogueService

def test_admin_can_disable_and_reenable_catalogue_entry(tmp_path):
    svc=LuthieryCatalogueService(str(tmp_path/"craft.db"))
    svc.ensure_schema()
    svc.set_enabled("material","luthier.material.basswood",False)
    assert all(x["key"]!="luthier.material.basswood" for x in svc.catalogue(100)["materials"])
    with pytest.raises(ValueError,match="not available"):
        svc.purchase(1,"luthier.material.basswood",1,100)
    svc.set_enabled("material","luthier.material.basswood",True)
    assert any(x["key"]=="luthier.material.basswood" for x in svc.catalogue(100)["materials"])

def test_admin_rejects_unknown_type_or_key(tmp_path):
    svc=LuthieryCatalogueService(str(tmp_path/"craft.db"))
    with pytest.raises(ValueError,match="Unsupported"):
        svc.set_enabled("bogus","x",False)
    with pytest.raises(ValueError,match="not found"):
        svc.set_enabled("material","missing",False)
