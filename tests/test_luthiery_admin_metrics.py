import sqlite3
from services import admin_analytics_service as analytics

def test_luthiery_metrics_report_quality_and_sales(tmp_path,monkeypatch):
 p=tmp_path/"metrics.db";monkeypatch.setattr(analytics,"DB_PATH",p)
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,quality_score REAL,quality_tier TEXT)")
  c.executemany("INSERT INTO crafted_items VALUES(?,?,?)",[(1,50,'Good'),(2,90,'Masterwork')])
  c.execute("CREATE TABLE luthier_shop_listings(id INTEGER PRIMARY KEY,status TEXT,price_cents INTEGER)")
  c.executemany("INSERT INTO luthier_shop_listings VALUES(?,?,?)",[(1,'active',10000),(2,'sold',25000)])
 out=analytics.fetch_luthiery_metrics()
 assert out["crafted_total"]==2 and out["avg_quality"]==70
 assert out["active_listings"]==1 and out["sold_listings"]==1 and out["gross_sales_cents"]==25000
