from typing import Any

import httpx

from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.utils.constants import DealSource
from amazon_deals_bot.utils.logger import logger

_BASE_URL = "https://api.magalu.com/maestro/v1"
_MIN_DISCOUNT_PCT = 15
_PAGE_SIZE = 50


class MagaluClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={"Authorization": f"Bearer {settings.magalu_token or ''}"},
            timeout=30.0,
        )

    async def fetch_deals(self) -> list[dict[str, Any]]:
        if not settings.magalu_token:
            logger.warning("magalu token not configured, skipping")
            return []

        try:
            response = await self._client.get(
                "/products",
                params={
                    "has_promotion": "true",
                    "page": 1,
                    "page_size": _PAGE_SIZE,
                    "sort": "discount_pct:desc",
                },
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(f"magalu api error: {exc.response.status_code}")
            return []
        except Exception as exc:
            logger.warning(f"magalu fetch failed: {exc}")
            return []

        results: list[dict[str, Any]] = []
        for product in data.get("results", []):
            parsed = self._parse_product(product)
            if parsed:
                results.append(parsed)

        logger.bind(event="magalu_fetch", count=len(results)).debug("magalu deals fetched")
        return results

    def _parse_product(self, product: dict[str, Any]) -> dict[str, Any] | None:
        name = product.get("name") or product.get("title")
        url = product.get("url")
        price_raw = product.get("price") or product.get("sale_price")
        original_raw = product.get("original_price") or product.get("regular_price")
        image_url = product.get("image") or product.get("thumbnail_url")

        if not (name and url and price_raw is not None):
            return None

        price = float(price_raw)
        original = float(original_raw) if original_raw else None

        if original and original > 0:
            discount = int(((original - price) / original) * 100)
            if discount < _MIN_DISCOUNT_PCT:
                return None

        return {
            "name": name,
            "price": price,
            "original_price": original,
            "url": url,
            "image_url": image_url,
            "source": DealSource.MAGALU,
        }

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "MagaluClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()