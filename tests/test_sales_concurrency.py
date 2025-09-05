import asyncio

from backend.services.sales_service import SalesService, SalesError
from backend.services.economy_service import EconomyService


def test_concurrent_vinyl_purchase(tmp_path):
    async def run():
        db = tmp_path / "sales.db"
        economy = EconomyService(db_path=db)
        economy.ensure_schema()

        sales = SalesService(db_path=db, economy=economy)
        await sales.ensure_schema()
        sku_id = await sales.create_vinyl_sku(album_id=1, variant="std", price_cents=1000, stock_qty=1)

        async def purchase():
            return await sales.purchase_vinyl(
                buyer_user_id=1, items=[{"sku_id": sku_id, "qty": 1}]
            )

        results = await asyncio.gather(purchase(), purchase(), return_exceptions=True)
        success = [r for r in results if isinstance(r, int)]
        failures = [r for r in results if isinstance(r, SalesError)]
        assert len(success) == 1
        assert len(failures) == 1

    asyncio.run(run())
