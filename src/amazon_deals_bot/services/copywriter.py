import openai
from sqlalchemy.ext.asyncio import AsyncSession

from amazon_deals_bot.clients.openai_client import OpenAIClient
from amazon_deals_bot.repositories.deal_repository import DealRepository
from amazon_deals_bot.services.affiliate import AffiliateService
from amazon_deals_bot.utils.constants import DealStatus
from amazon_deals_bot.utils.logger import logger


def _fallback_copy(deal, affiliate_url: str) -> str:
    """Simple template-based copy used when OpenAI is unavailable."""
    return (
        f"Oferta imperdivel!\n\n"
        f"{deal.name}\n\n"
        f"De: R${deal.original_price:.2f}\n"
        f"Por: R${deal.price:.2f}\n"
        f"Desconto: {deal.discount_pct}%\n\n"
        f"Confira agora: {affiliate_url}"
    )


class CopywriterService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DealRepository(session)
        self.openai_client = OpenAIClient()
        self.affiliate_service = AffiliateService()

    async def process(self) -> int:
        deals = await self.repo.get_pending_deals(limit=10)
        processed_count = 0

        for deal in deals:
            # Build the affiliate URL first — used both for copy generation and storage
            affiliate_url = AffiliateService.build_link(deal.url, deal.source)

            # Persist the affiliate URL on the in-memory object so SQLAlchemy
            # tracks the dirty attribute and commits it together with update_copy.
            deal.affiliate_url = affiliate_url

            try:
                copy = await self.openai_client.generate_copy(
                    deal_name=deal.name,
                    price=float(deal.price),
                    original_price=float(deal.original_price),
                    discount_pct=deal.discount_pct,
                    source=deal.source,
                    affiliate_url=affiliate_url,
                )
                logger.bind(event="copy_generated", deal_id=deal.id).info(
                    "openai copy generated"
                )

            except openai.OpenAIError as exc:
                new_retry = (deal.retry_count or 0) + 1
                logger.warning(
                    f"openai failed for deal {deal.id} (retry {new_retry}): {exc}"
                )

                if new_retry >= 3:
                    await self.repo.update_status(
                        deal.id, DealStatus.FAILED, retry_count=new_retry
                    )
                    logger.warning(f"deal {deal.id} exhausted retries, marked FAILED")
                    continue

                # Use fallback copy so the deal can still go out
                copy = _fallback_copy(deal, affiliate_url)
                logger.bind(event="copy_fallback", deal_id=deal.id).info(
                    "using fallback copy template"
                )

            except Exception as exc:
                new_retry = (deal.retry_count or 0) + 1
                logger.exception(
                    f"unexpected error generating copy for deal {deal.id} "
                    f"(retry {new_retry}): {exc}"
                )

                if new_retry >= 3:
                    await self.repo.update_status(
                        deal.id, DealStatus.FAILED, retry_count=new_retry
                    )
                    continue

                copy = _fallback_copy(deal, affiliate_url)
                logger.bind(event="copy_fallback", deal_id=deal.id).info(
                    "using fallback copy template after unexpected error"
                )

            # update_copy sets status=READY and commits; the dirty affiliate_url
            # on the Deal object is flushed in the same commit via SQLAlchemy tracking.
            await self.repo.update_copy(deal.id, copy)
            processed_count += 1
            logger.bind(event="deal_ready", deal_id=deal.id).info("deal marked READY")

        return processed_count