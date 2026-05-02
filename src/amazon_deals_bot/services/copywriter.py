from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from amazon_deals_bot.models.deal import Deal
from amazon_deals_bot.repositories.deal_repository import DealRepository


class CopywriterService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DealRepository(session)

    async def get_pending_deals(self, limit: int = 10):
        result = await self.session.execute(
            select(Deal).where(Deal.status == "PENDING").limit(limit)
        )
        return result.scalars().all()

    async def generate_copy(self, deal: Deal) -> str:
        """
        Placeholder de IA (vamos integrar OpenAI depois)
        """
        return f"""🔥 OFERTA IMPERDÍVEL!

{deal.name}

💰 De: R${deal.original_price}
💸 Por: R${deal.price}

🚨 Desconto: {deal.discount_pct}%

👉 Confira agora: {deal.url}
"""

    async def process(self):
        deals = await self.get_pending_deals()

        for deal in deals:
            try:
                copy = await self.generate_copy(deal)

                deal.copy = copy
                deal.status = "READY"

                await self.session.commit()

            except Exception:
                deal.status = "FAILED"
                await self.session.commit()