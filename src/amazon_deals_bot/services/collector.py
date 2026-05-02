from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from amazon_deals_bot.models.deal import Deal
from amazon_deals_bot.repositories.deal_repository import DealRepository
from amazon_deals_bot.services.deduplicator import DeduplicatorService


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

        # 1. Normalizar URL
        normalized_url = DeduplicatorService.normalize_url(url)

        # 2. Gerar ID (hash)
        deal_id = DeduplicatorService.generate_deal_id(
            normalized_url,
            price,
        )

        # 3. Verificar duplicidade
        exists = await self.repo.exists(deal_id)
        if exists:
            return None

        # 4. Calcular desconto
        discount_pct = None
        if price and original_price and original_price > 0:
            discount_pct = int(
                ((original_price - price) / original_price) * 100
            )

        # 5. Criar objeto Deal
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

        # 6. Salvar no banco
        await self.repo.create(deal)

        return deal