from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from amazon_deals_bot.clients.amazon import AmazonClient
from amazon_deals_bot.clients.magalu import MagaluClient
from amazon_deals_bot.clients.shopee import ShopeeClient
from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.models.deal import Deal
from amazon_deals_bot.repositories.deal_repository import DealRepository
from amazon_deals_bot.services.deduplicator import DeduplicatorService
from amazon_deals_bot.utils.logger import logger


class CollectorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DealRepository(session)

    async def process_product(
        self,
        name: str,
        price: Optional[float],
        original_price: Optional[float],
        url: str,
        image_url: Optional[str],
        source: str,
    ) -> Optional[Deal]:

        normalized_url = DeduplicatorService.normalize_url(url)
        deal_id = DeduplicatorService.generate_deal_id(normalized_url, price)

        if await self.repo.exists(deal_id):
            return None

        discount_pct = None
        if price and original_price and original_price > 0:
            discount_pct = int(((original_price - price) / original_price) * 100)

        deal = Deal(
            id=deal_id,
            name=name,
            price=price,
            original_price=original_price,
            discount_pct=discount_pct,
            url=normalized_url,
            image_url=image_url,
            source=source,
            status="PENDING",
        )

        await self.repo.create(deal)
        return deal

    async def run(self) -> int:
        total = 0

        # Amazon PA-API
        if settings.amazon_pa_api_access_key:
            async with AmazonClient() as client:
                products = await client.fetch_deals()
            for p in products:
                deal = await self.process_product(**p)
                if deal:
                    total += 1
                    logger.bind(event="deal_collected", source="amazon", deal_id=deal.id).info(
                        "new deal persisted"
                    )

        # Shopee Open Platform
        if settings.shopee_app_id and settings.shopee_secret:
            async with ShopeeClient() as client:
                products = await client.fetch_deals()
            for p in products:
                deal = await self.process_product(**p)
                if deal:
                    total += 1
                    logger.bind(event="deal_collected", source="shopee", deal_id=deal.id).info(
                        "new deal persisted"
                    )

        # Magalu Parceiros
        if settings.magalu_token:
            async with MagaluClient() as client:
                products = await client.fetch_deals()
            for p in products:
                deal = await self.process_product(**p)
                if deal:
                    total += 1
                    logger.bind(event="deal_collected", source="magalu", deal_id=deal.id).info(
                        "new deal persisted"
                    )

        logger.bind(event="collector_run", total=total).info("collector run complete")
        return total