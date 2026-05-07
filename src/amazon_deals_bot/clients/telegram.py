import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.utils.logger import logger


class TelegramBotClient:
    def __init__(self):
        if settings.telegram_bot_token is None:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
        self._bot = telegram.Bot(token=settings.telegram_bot_token)

    async def send_message(self, channel_id: str, text: str) -> bool:
        try:
            await self._bot.send_message(
                chat_id=channel_id,
                text=text,
            )
            logger.bind(event="telegram_sent", channel_id=channel_id).info("message sent")
            return True
        except telegram.error.TelegramError as exc:
            logger.warning(f"telegram send_message failed for {channel_id}: {exc}")
            return False

    async def send_photo(
        self, channel_id: str, photo_url: str, caption: str, link: str
    ) -> bool:
        if not photo_url:
            return await self.send_message(channel_id, caption)

        try:
            await self._bot.send_photo(
                chat_id=channel_id,
                photo=photo_url,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🛒 Comprar agora", url=link)]]
                ),
            )
            logger.bind(event="telegram_sent", channel_id=channel_id).info("photo sent")
            return True
        except telegram.error.TelegramError as exc:
            logger.warning(f"telegram send_photo failed for {channel_id}: {exc}")
            return False