import asyncio
import random
import time
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from amazon_deals_bot.clients.evolution import EvolutionClient
from amazon_deals_bot.clients.telegram import TelegramBotClient
from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.db.redis import redis_client
from amazon_deals_bot.repositories.deal_repository import DealRepository
from amazon_deals_bot.utils.constants import DealStatus
from amazon_deals_bot.utils.logger import logger

_WPP_LAST_SENT_KEY = "wpp:last_sent"
_WPP_DAILY_COUNT_KEY = "wpp:daily_count:{date}"


class PublisherService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = DealRepository(session)
        self.evolution = EvolutionClient()
        # Telegram client is optional — only instantiate when configured
        self._telegram: TelegramBotClient | None = None
        if settings.telegram_channel_id and settings.telegram_bot_token:
            try:
                self._telegram = TelegramBotClient()
            except ValueError as exc:
                logger.warning(f"TelegramBotClient not initialised: {exc}")

    # ------------------------------------------------------------------
    # Rate-limiting helpers
    # ------------------------------------------------------------------

    async def _wpp_check_rate_limits(self) -> bool:
        """
        Returns True when the current moment is within rate-limit budget.
        Logs the reason and returns False when any guard trips.
        """
        now = time.time()
        current_hour = datetime.now(tz=timezone.utc).hour

        # 1. Active-hours guard
        if not (settings.wpp_active_hours_start <= current_hour < settings.wpp_active_hours_end):
            logger.debug(
                f"wpp outside active hours (hour={current_hour}, "
                f"window={settings.wpp_active_hours_start}-{settings.wpp_active_hours_end})"
            )
            return False

        # 2. Daily-cap guard
        date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        daily_key = _WPP_DAILY_COUNT_KEY.format(date=date_str)
        raw_count = await redis_client.get(daily_key)
        daily_count = int(raw_count) if raw_count else 0

        if daily_count >= settings.wpp_daily_cap:
            logger.warning(
                f"wpp daily cap reached ({daily_count}/{settings.wpp_daily_cap})",
                extra={"event": "wpp_daily_cap"},
            )
            return False

        # 3. Min-interval guard
        raw_last = await redis_client.get(_WPP_LAST_SENT_KEY)
        if raw_last is not None:
            elapsed = now - float(raw_last)
            if elapsed < settings.wpp_min_interval_seconds:
                logger.debug(
                    f"wpp rate-limit: {elapsed:.1f}s since last send "
                    f"(min={settings.wpp_min_interval_seconds}s)"
                )
                return False

        return True

    async def _wpp_record_sent(self) -> None:
        """Persist the send timestamp and increment the daily counter."""
        now = time.time()
        date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        daily_key = _WPP_DAILY_COUNT_KEY.format(date=date_str)

        await redis_client.set(_WPP_LAST_SENT_KEY, now)
        await redis_client.incr(daily_key)
        # Ensure the key expires at midnight + a small buffer
        await redis_client.expire(daily_key, 86400)

    # ------------------------------------------------------------------
    # Channel senders
    # ------------------------------------------------------------------

    async def _send_telegram(self, deal) -> bool:
        if self._telegram is None or not settings.telegram_channel_id:
            return False

        channel_id = settings.telegram_channel_id
        affiliate_url = deal.affiliate_url or deal.url

        if deal.image_url:
            ok = await self._telegram.send_photo(
                channel_id=channel_id,
                photo_url=deal.image_url,
                caption=deal.copy,
                link=affiliate_url,
            )
        else:
            ok = await self._telegram.send_message(
                channel_id=channel_id,
                text=deal.copy,
            )

        if ok:
            logger.bind(event="telegram_sent", deal_id=deal.id).info("deal sent to telegram")
        else:
            logger.warning(f"telegram send failed for deal {deal.id}")

        return ok

    async def _send_whatsapp(self, deal) -> bool:
        """Send deal to all configured WhatsApp groups, honouring rate limits."""
        groups = settings.wpp_group_id_list
        if not groups:
            logger.debug("no wpp groups configured, skipping")
            return False

        at_least_one_ok = False

        for group_id in groups:
            allowed = await self._wpp_check_rate_limits()
            if not allowed:
                logger.debug(f"wpp rate-limit blocked send to {group_id} for deal {deal.id}")
                continue

            if deal.image_url:
                ok = await self.evolution.send_media(
                    group_id=group_id,
                    image_url=deal.image_url,
                    caption=deal.copy,
                )
            else:
                ok = await self.evolution.send_text(
                    group_id=group_id,
                    text=deal.copy,
                )

            if ok:
                await self._wpp_record_sent()
                logger.bind(event="wpp_sent", deal_id=deal.id, group_id=group_id).info(
                    "deal sent to whatsapp"
                )
                at_least_one_ok = True
            else:
                logger.warning(f"wpp send failed for deal {deal.id} -> group {group_id}")

        return at_least_one_ok

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self) -> int:
        deals = await self.repo.get_ready_deals(limit=5)
        sent_count = 0

        for deal in deals:
            if not deal.copy:
                logger.warning(f"deal {deal.id} has no copy, skipping")
                continue

            try:
                telegram_ok = await self._send_telegram(deal)
                wpp_ok = await self._send_whatsapp(deal)

                if telegram_ok or wpp_ok:
                    await self.repo.update_status(deal.id, DealStatus.SENT)
                    sent_count += 1
                    logger.bind(event="deal_sent", deal_id=deal.id).info("deal marked SENT")
                else:
                    new_retry = (deal.retry_count or 0) + 1
                    if new_retry >= 3:
                        await self.repo.update_status(
                            deal.id, DealStatus.FAILED, retry_count=new_retry
                        )
                        logger.warning(
                            f"deal {deal.id} exhausted retries, marked FAILED"
                        )
                    else:
                        await self.repo.update_status(
                            deal.id, DealStatus.READY, retry_count=new_retry
                        )
                        logger.debug(
                            f"deal {deal.id} returned to READY queue (retry {new_retry})"
                        )

            except Exception as exc:
                logger.exception(f"unexpected error processing deal {deal.id}: {exc}")
                new_retry = (deal.retry_count or 0) + 1
                if new_retry >= 3:
                    await self.repo.update_status(
                        deal.id, DealStatus.FAILED, retry_count=new_retry
                    )
                else:
                    await self.repo.update_status(
                        deal.id, DealStatus.READY, retry_count=new_retry
                    )

            finally:
                # Anti-ban jitter between every deal regardless of outcome
                sleep_secs = random.uniform(
                    settings.wpp_min_interval_seconds,
                    settings.wpp_max_interval_seconds,
                )
                logger.debug(f"sleeping {sleep_secs:.1f}s before next deal (anti-ban)")
                await asyncio.sleep(sleep_secs)

        return sent_count

    async def close(self) -> None:
        await self.evolution.close()