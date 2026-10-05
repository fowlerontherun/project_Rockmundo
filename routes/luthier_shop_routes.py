from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from auth.character_dependencies import get_current_character_id
from services.luthier_shop_service import luthier_shop_service
router=APIRouter(prefix="/luthiery/shops",tags=["Luthiery Shops"])
class ShopIn(BaseModel):
 name:str
 description:str=""
 city_id:int|None=None
class ListingIn(BaseModel):
 item_id:int
 price_cents:int
@router.put("/mine")
def save_shop(payload:ShopIn,character_id:int=Depends(get_current_character_id)):
 try:return luthier_shop_service.save_shop(character_id,payload.name,payload.description,payload.city_id)
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
@router.get("/mine")
def my_shop(character_id:int=Depends(get_current_character_id)):
 return luthier_shop_service.mine(character_id)
@router.delete("/mine/listings/{listing_id}")
def withdraw_listing(listing_id:int,character_id:int=Depends(get_current_character_id)):
 try:luthier_shop_service.withdraw(character_id,listing_id);return {"ok":True}
 except ValueError as e:raise HTTPException(status_code=404,detail=str(e)) from e
@router.post("/mine/listings")
def list_instrument(payload:ListingIn,character_id:int=Depends(get_current_character_id)):
 try:return luthier_shop_service.list_item(character_id,payload.item_id,payload.price_cents)
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
@router.get("")
def browse_shops():return {"items":luthier_shop_service.browse()}
@router.get("/listings/{listing_id}")
def listing_detail(listing_id:int):
 try:return luthier_shop_service.listing_detail(listing_id)
 except ValueError as e:raise HTTPException(status_code=404,detail=str(e)) from e
@router.post("/listings/{listing_id}/purchase")
def purchase(listing_id:int,character_id:int=Depends(get_current_character_id)):
 try:return luthier_shop_service.purchase(character_id,listing_id)
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
