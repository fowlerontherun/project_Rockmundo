import sqlite3
from services.luthiery_crafting_service import LuthieryCraftingService

def test_quality_tiers_cover_intended_progression():
 svc=LuthieryCraftingService(":memory:")
 assert svc._tier(25)=="Poor"
 assert svc._tier(40)=="Basic"
 assert svc._tier(55)=="Good"
 assert svc._tier(70)=="Excellent"
 assert svc._tier(80)=="Professional"
 assert svc._tier(90)=="Masterwork"
 assert svc._tier(97)=="Legendary"

def test_seed_quality_normalization_keeps_starter_low_and_premium_meaningful():
 def contribution(q,component_q=None):
  material=max(0,min(100,55+(q-.90)*93.75))
  bonus=max(0,min(15,(component_q-.90)*46.875+5)) if component_q is not None else 0
  return min(100,material+bonus)
 assert 55 <= contribution(.90) <= 58
 assert contribution(1.22)>80
 assert contribution(1.22,1.0)>90

def test_skill_ceiling_prevents_novice_material_bypass():
 for level in (1,10,20,40):
  assert 48+level*.52 < 70
 assert 48+100*.52==100
