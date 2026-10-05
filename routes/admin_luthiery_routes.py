"""Admin controls for Luthiery live operations."""
import sqlite3
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from auth.dependencies import get_current_user_id,require_permission
from services.luthiery_catalogue_service import luthiery_catalogue_service,DB_PATH
from services.luthiery_reputation_service import luthiery_reputation\nfrom services.luthiery_balance_service import balance_service\nfrom services.luthiery_crafting_service import luthiery_crafting_service

router=APIRouter(prefix="/admin/luthiery",tags=["Admin Luthiery"])
async def _admin(user_id:int=Depends(get_current_user_id))->int:
 await require_permission(["admin"],user_id);return user_id
class EnabledUpdate(BaseModel): enabled:bool
class QualityWeightsUpdate(BaseModel):\n skill:float\n materials:float\n specialist:float\n workshop:float\n variance:float\nclass TraitUpdate(BaseModel): enabled:bool\nclass FeatureUpdate(BaseModel): enabled:bool\nclass DemoPart(BaseModel):
 material_key:str
 component_key:str|None=None
class CraftDemoRequest(BaseModel):
 instrument_type:str
 shape_key:str
 selections:dict[str,DemoPart]
 skills:dict[str,float]
 finish_key:str="luthier.finish.solid"
 workshop_score:float=50
 seed_token:str="admin-demo"
class CraftBatchRequest(CraftDemoRequest):
 samples:int=100
class CatalogueBalanceUpdate(BaseModel):
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

@router.post("/demo/craft")
def demo_craft(payload:CraftDemoRequest,_admin_id:int=Depends(_admin)):
 try:
  return luthiery_crafting_service.admin_preview(payload.instrument_type,payload.shape_key,{k:v.model_dump() for k,v in payload.selections.items()},payload.skills,payload.finish_key,payload.workshop_score,payload.seed_token)
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc

@router.post("/demo/batch")
def demo_batch(payload:CraftBatchRequest,_admin_id:int=Depends(_admin)):
 if payload.samples<1 or payload.samples>1000:raise HTTPException(status_code=400,detail="Samples must be between 1 and 1000")
 tiers={};traits={};scores=[];examples=[]
 try:
  selections={k:v.model_dump() for k,v in payload.selections.items()}
  for i in range(payload.samples):
   result=luthiery_crafting_service.admin_preview(payload.instrument_type,payload.shape_key,selections,payload.skills,payload.finish_key,payload.workshop_score,f"{payload.seed_token}:{i}")
   score=float(result["quality_score"]);scores.append(score);tiers[result["quality_tier"]]=tiers.get(result["quality_tier"],0)+1
   for trait in result.get("traits",[]):traits[trait]=traits.get(trait,0)+1
   if i<5:examples.append(result)
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
 return {"samples":payload.samples,"quality":{"min":min(scores),"max":max(scores),"average":round(sum(scores)/len(scores),2)},"tiers":tiers,"traits":traits,"examples":examples}

@router.post("/demo/matrix")
def demo_matrix(payload:CraftBatchRequest,_admin_id:int=Depends(_admin)):
 samples=min(max(payload.samples,1),500)
 presets={"Novice":10,"Competent":50,"Master":100};rows=[]
 selections={k:v.model_dump() for k,v in payload.selections.items()}
 try:
  for label,level in presets.items():
   skills={k:level for k in ("luthiery","woodworking","fretwork","instrument_electronics","instrument_finishing")}
   scores=[];tiers={}
   for i in range(samples):
    r=luthiery_crafting_service.admin_preview(payload.instrument_type,payload.shape_key,selections,skills,payload.finish_key,payload.workshop_score,f"matrix:{label}:{i}")
    scores.append(float(r["quality_score"]));tiers[r["quality_tier"]]=tiers.get(r["quality_tier"],0)+1
   rows.append({"preset":label,"level":level,"average":round(sum(scores)/len(scores),2),"min":min(scores),"max":max(scores),"tiers":tiers})
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
 warnings=[]
 by={x["preset"]:x for x in rows}
 novice_high=sum(v for k,v in by["Novice"]["tiers"].items() if k in ("Masterwork","Legendary"))/samples
 master_low=sum(v for k,v in by["Master"]["tiers"].items() if k in ("Poor","Basic","Good"))/samples
 if novice_high>.01:warnings.append("Novices produce Masterwork/Legendary instruments too frequently.")
 if master_low>.10:warnings.append("Master Luthiers produce low-tier instruments too frequently.")
 if by["Master"]["average"]-by["Competent"]["average"]<10:warnings.append("Master progression has less than a 10-point average quality advantage over Competent.")
 return {"samples_per_preset":samples,"rows":rows,"warnings":warnings}

@router.post("/demo/recipe-sweep")
def demo_recipe_sweep(payload:CraftBatchRequest,_admin_id:int=Depends(_admin)):
 samples=min(max(payload.samples,1),250);base={k:v.model_dump() for k,v in payload.selections.items()};rows=[]
 luthiery_crafting_service.ensure_schema()
 with sqlite3.connect(DB_PATH) as c:
  c.row_factory=sqlite3.Row
  materials=[dict(x) for x in c.execute("SELECT key,name FROM crafting_materials WHERE enabled=1 ORDER BY required_level,key")]
 for material in materials:
  scores=[];valid=True
  candidate={k:dict(v) for k,v in base.items()};candidate["body"]["material_key"]=material["key"]
  try:
   for i in range(samples):
    r=luthiery_crafting_service.admin_preview(payload.instrument_type,payload.shape_key,candidate,payload.skills,payload.finish_key,payload.workshop_score,f"sweep:{material['key']}:{i}")
    scores.append(float(r["quality_score"]))
  except ValueError:valid=False
  if valid:rows.append({"material_key":material["key"],"material_name":material["name"],"average":round(sum(scores)/len(scores),2),"min":min(scores),"max":max(scores)})
 rows.sort(key=lambda x:x["average"],reverse=True);warnings=[]
 if len(rows)>1:
  spread=rows[0]["average"]-rows[-1]["average"]
  if spread<2:warnings.append("Body material choice changes average quality by less than 2 points; material progression may feel insignificant.")
  if spread>20:warnings.append("Body material choice changes average quality by more than 20 points; premium materials may be overly dominant.")
 return {"samples_per_material":samples,"rows":rows,"warnings":warnings}
