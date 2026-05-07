import httpx
from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.utils.logger import logger
from amazon_deals_bot.utils.retry import retry_api


class EvolutionClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.evolution_api_url,
            headers={"apikey": settings.evolution_api_key},
            timeout=30.0,
        )
        self._instance = settings.evolution_instance_name

    async def send_text(self, group_id: str, text: str) -> bool:
        @retry_api
        async def _call():
            return await self._client.post(
                f"/message/sendText/{self._instance}",
                json={"number": group_id, "text": text},
            )

        try:
            response = await _call()
            response.raise_for_status()
            logger.bind(event="wpp_sent", group_id=group_id).info("text message sent")
            return True
        except Exception as exc:
            logger.warning(f"evolution send_text failed for {group_id}: {exc}")
            return False

    async def send_media(self, group_id: str, image_url: str, caption: str) -> bool:
        @retry_api
        async def _call():
            return await self._client.post(
                f"/message/sendMedia/{self._instance}",
                json={
                    "number": group_id,
                    "mediatype": "image",
                    "media": image_url,
                    "caption": caption,
                },
            )

        try:
            response = await _call()
            response.raise_for_status()
            logger.bind(event="wpp_sent", group_id=group_id).info("media message sent")
            return True
        except Exception as exc:
            logger.warning(f"evolution send_media failed for {group_id}: {exc}")
            return False

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()