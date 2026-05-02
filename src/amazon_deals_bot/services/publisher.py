import asyncio
import random

from sqlalchemy.ext.asyncio import AsyncSession

from amazon_deals_bot.repositories.deal_repository import DealRepository


class PublisherService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DealRepository(session)

    async def send_to_telegram(self, message: str):
        # TODO: integrar API real depois
        print("📢 TELEGRAM:")
        print(message)

    async def send_to_whatsapp(self, message: str):
        # TODO: integrar Evolution API depois
        print("📱 WHATSAPP:")
        print(message)

    async def process(self):
        deals = await self.repo.get_ready_deals(limit=5)

        for deal in deals:
            try:
                if not deal.copy:
                    continue

                message = deal.copy

                # envio
                await self.send_to_telegram(message)
                await self.send_to_whatsapp(message)

                # status
                await self.repo.update_status(deal.id, "SENT")

                # 🔥 anti-ban (CRÍTICO)
                await asyncio.sleep(random.randint(45, 90))

            except Exception:
                new_retry = (deal.retry_count or 0) + 1

                # 🔥 controle de retry
                if new_retry >= 3:
                    await self.repo.update_status(
                        deal.id,
                        "FAILED",
                        retry_count=new_retry,
                    )
                else:
                    await self.repo.update_status(
                        deal.id,
                        "READY",  # volta pra fila
                        retry_count=new_retry,
                    )