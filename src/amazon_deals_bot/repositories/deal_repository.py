from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from amazon_deals_bot.models.deal import Deal


class DealRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, deal_id: str) -> Deal | None:
        result = await self.session.execute(
            select(Deal).where(Deal.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def exists(self, deal_id: str) -> bool:
        result = await self.session.execute(
            select(Deal.id).where(Deal.id == deal_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, deal: Deal) -> Deal:
        self.session.add(deal)
        await self.session.commit()
        await self.session.refresh(deal)
        return deal

    async def get_pending_deals(self, limit: int = 10):
        result = await self.session.execute(
            select(Deal).where(Deal.status == "PENDING").limit(limit)
        )
        return result.scalars().all()

    async def get_ready_deals(self, limit: int = 10):
        result = await self.session.execute(
            select(Deal).where(Deal.status == "READY").limit(limit)
        )
        return result.scalars().all()

    async def update_status(
        self,
        deal_id: str,
        status: str,
        retry_count: int | None = None,
    ):
        deal = await self.get_by_id(deal_id)
        if not deal:
            return None

        deal.status = status
        deal.updated_at = datetime.now(timezone.utc)

        if status == "SENT":
            deal.sent_at = datetime.now(timezone.utc)

        if retry_count is not None:
            deal.retry_count = retry_count

        await self.session.commit()
        await self.session.refresh(deal)
        return deal

    async def update_copy(self, deal_id: str, copy: str):
        deal = await self.get_by_id(deal_id)
        if not deal:
            return None

        deal.copy = copy
        deal.status = "READY"
        deal.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(deal)
        return deal