"""Admin controls for Luthiery live operations."""
import sqlite3
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from auth.dependencies import get_current_user_id,require_permission
from services.luthiery_catalogue_service import luthiery_catalogue_service,DB_PATH
from services.luthiery_reputation_service import luthiery_reputation\nfrom services.luthiery_balance_service import balance_service

router=APIRouter(prefix="/admin/luthiery",tags=["Admin Luthiery"])
async def _admin(user_id:int=Depends(get_current_user_id))->int:
 await require_permission(["admin"],user_id);return user_id
class EnabledUpdate(BaseModel): enabled:bool
class QualityWeightsUpdate(BaseModel):\n skill:float\n materials:float\n specialist:float\n workshop:float\n variance:float\nclass TraitUpdate(BaseModel): enabled:bool\nclass FeatureUpdate(BaseModel): enabled:bool\nclass CatalogueBalanceUpdate(BaseModel):
 required_level:int|None=None
 cost_cents:int|None=None
 stock:int|None=None

@router.get("/catalogue")
def catalogue(_admin_id:int=Depends(_admin)):return luthiery_catalogue_service.admin_catalogue()
@router.put("/catalogue/{content_type}/{content_key}/enabled")
def set_enabled(content_type:str,content_key:str,payload:EnabledUpdate,_admin_id:int=Depends(_admin)):
 try:luthiery_catalogue_service.set_enabled(content_type,content_key,payload.enabled)
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
 return {"status":"ok","enabled":payload.enabled}
@router.patch("/catalogue/{content_type}/{content_key}")
def update_catalogue(content_type:str,content_key:str,payload:CatalogueBalanceUpdate,_admin_id:int=Depends(_admin)):
 try:return luthiery_catalogue_service.admin_update(content_type,content_key,payload.required_level,payload.cost_cents,payload.stock)
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
@router.get("/items/{serial_number}")
def lookup_serial(serial_number:str,_admin_id:int=Depends(_admin)):
 luthiery_reputation.ensure_schema()
 with sqlite3.connect(DB_PATH) as conn:
  conn.row_factory=sqlite3.Row
  item=conn.execute("SELECT * FROM crafted_items WHERE serial_number=?",(serial_number,)).fetchone()
  if not item:raise HTTPException(status_code=404,detail="Crafted instrument not found")
  out=dict(item);iid=int(item["id"])
  out["events"]=[dict(x) for x in conn.execute("SELECT * FROM crafted_item_events WHERE crafted_item_id=? ORDER BY id",(iid,))]
  out["notable_history"]=luthiery_reputation.item_history(iid);out["desirability"]=luthiery_reputation.desirability(iid)
  return out

@router.get("/balance/quality")
def get_quality(_admin_id:int=Depends(_admin)):return balance_service.quality_weights()
@router.put("/balance/quality")
def set_quality(payload:QualityWeightsUpdate,_admin_id:int=Depends(_admin)):
 try:return balance_service.set_quality_weights(payload.model_dump())
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
@router.put("/traits/{trait_key}")
def set_trait(trait_key:str,payload:TraitUpdate,_admin_id:int=Depends(_admin)):
 balance_service.set_trait(trait_key,payload.enabled);return {"trait_key":trait_key,"enabled":payload.enabled}
@router.get("/suspicious")
def suspicious(_admin_id:int=Depends(_admin)):
 with sqlite3.connect(DB_PATH) as c:
  c.row_factory=sqlite3.Row;findings=[]
  try:
   findings += [dict(x)|{"signal":"repeat_buyer_seller"} for x in c.execute("""SELECT seller_character_id,buyer_character_id,COUNT(*) count,SUM(price_cents) value_cents FROM luthier_shop_listings WHERE status='sold' GROUP BY seller_character_id,buyer_character_id HAVING COUNT(*)>=5 ORDER BY count DESC LIMIT 50""")]
   findings += [dict(x)|{"signal":"extreme_price"} for x in c.execute("""SELECT id listing_id,seller_character_id,buyer_character_id,price_cents FROM luthier_shop_listings WHERE status='sold' AND price_cents>=10000000 ORDER BY price_cents DESC LIMIT 50""")]
  except sqlite3.OperationalError:pass
  return {"findings":findings}

@router.get("/features")
def features(_admin_id:int=Depends(_admin)):
 return {"legendary_shapes":balance_service.feature_enabled("legendary_shapes"),"premium_materials":balance_service.feature_enabled("premium_materials"),"boutique_electronics":balance_service.feature_enabled("boutique_electronics"),"metallic_finishes":balance_service.feature_enabled("metallic_finishes")}
@router.put("/features/{feature_key}")
def set_feature(feature_key:str,payload:FeatureUpdate,_admin_id:int=Depends(_admin)):
 try:return balance_service.set_feature(feature_key,payload.enabled)
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
