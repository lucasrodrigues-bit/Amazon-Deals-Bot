from sqlalchemy.ext.asyncio import AsyncSession

from amazon_deals_bot.models.deal import Deal
from amazon_deals_bot.repositories.deal_repository import DealRepository


class CopywriterService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DealRepository(session)

    async def generate_copy(self, deal: Deal) -> str:
        """
        Placeholder (depois entra OpenAI)
        """
        return f"""🔥 OFERTA IMPERDÍVEL!

{deal.name}

💰 De: R${deal.original_price}
💸 Por: R${deal.price}

🚨 Desconto: {deal.discount_pct}%

👉 Confira agora: {deal.url}
"""

    async def process(self):
        # 🔥 agora via repository
        deals = await self.repo.get_pending_deals(limit=10)

        for deal in deals:
            try:
                copy = await self.generate_copy(deal)

                # 🔥 atualização centralizada
                await self.repo.update_copy(deal.id, copy)

            except Exception:
                new_retry = (deal.retry_count or 0) + 1

                if new_retry >= 3:
                    await self.repo.update_status(
                        deal.id,
                        "FAILED",
                        retry_count=new_retry,
                    )
                else:
                    await self.repo.update_status(
                        deal.id,
                        "PENDING",
                        retry_count=new_retry,
                    )