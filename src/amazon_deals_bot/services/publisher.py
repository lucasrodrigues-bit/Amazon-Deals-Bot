import asyncio
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from amazon_deals_bot.models.deal import Deal
from amazon_deals_bot.repositories.deal_repository import DealRepository


class PublisherService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DealRepository(session)

    async def get_ready_deals(self, limit: int = 5):
        result = await self.session.execute(
            select(Deal).where(Deal.status == "READY").limit(limit)
        )
        return result.scalars().all()

    async def send_to_telegram(self, message: str):
        """
        Placeholder (vamos integrar depois)
        """
        print("📢 TELEGRAM:")
        print(message)

    async def send_to_whatsapp(self, message: str):
        """
        Placeholder (Evolution API depois)
        """
        print("📱 WHATSAPP:")
        print(message)

    async def process(self):
        deals = await self.get_ready_deals()

        for deal in deals:
            try:
                message = deal.copy

                if not message:
                    continue

                # envio
                await self.send_to_telegram(message)
                await self.send_to_whatsapp(message)

                # status
                deal.status = "SENT"

                await self.session.commit()

                # anti-spam (CRÍTICO)
                await asyncio.sleep(random.randint(45, 90))

            except Exception:
                deal.status = "FAILED"
                deal.retry_count += 1

                await self.session.commit()