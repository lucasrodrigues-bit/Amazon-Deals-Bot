import hashlib
import hmac
import time
from typing import Any

import httpx

from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.utils.constants import DealSource
from amazon_deals_bot.utils.logger import logger

_BASE_URL = "https://partner.shopeemobile.com"
_MIN_DISCOUNT_PCT = 15


def _sign(partner_key: str, partner_id: str, path: str, timestamp: int) -> str:
    base_string = f"{partner_id}{path}{timestamp}"
    return hmac.new(
        partner_key.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _common_params(partner_id: str, partner_key: str, path: str) -> dict[str, Any]:
    ts = int(time.time())
    return {
        "partner_id": int(partner_id),
        "timestamp": ts,
        "sign": _sign(partner_key, partner_id, path, ts),
    }


class ShopeeClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(base_url=_BASE_URL, timeout=30.0)
        self._partner_id = settings.shopee_app_id or ""
        self._partner_key = settings.shopee_secret or ""

    async def _get_active_flash_sale_id(self) -> int | None:
        path = "/api/v2/flash_sale/get_flash_sale_list"
        params = self._common_params(path)
        params["page_no"] = 1
        params["page_size"] = 5
        params["need_ongoing_items"] = True

        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            data = response.json()

            flash_sales = data.get("response", {}).get("flash_sale", [])
            if not flash_sales:
                return None

            # Prefer the one currently active (status=1)
            for fs in flash_sales:
                if fs.get("status") == 1:
                    return fs.get("flash_sale_id")
            return None

        except Exception as exc:
            logger.warning(f"shopee get_flash_sale_list failed: {exc}")
            return None

    def _common_params(self, path: str) -> dict[str, Any]:
        return _common_params(self._partner_id, self._partner_key, path)

    async def _get_flash_sale_items(self, flash_sale_id: int) -> list[dict[str, Any]]:
        path = "/api/v2/flash_sale/get_flash_sale_item_list"
        params = self._common_params(path)
        params["flash_sale_id"] = flash_sale_id
        params["page_no"] = 1
        params["page_size"] = 50

        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("response", {}).get("items", [])
        except Exception as exc:
            logger.warning(f"shopee get_flash_sale_item_list failed: {exc}")
            return []

    def _parse_item(self, item: dict[str, Any]) -> dict[str, Any] | None:
        name = item.get("name")
        item_id = item.get("item_id")
        shop_id = item.get("shop_id")
        price_before_discount = item.get("price_before_discount")
        price = item.get("price")
        image = item.get("image")

        if not (name and item_id and shop_id and price is not None):
            return None

        # Shopee prices are in smallest unit (cents × 100000)
        price_float = float(price) / 100_000
        original_float = float(price_before_discount) / 100_000 if price_before_discount else None

        if original_float and original_float > 0:
            discount = int(((original_float - price_float) / original_float) * 100)
            if discount < _MIN_DISCOUNT_PCT:
                return None

        url = f"https://shopee.com.br/product/{shop_id}/{item_id}"
        image_url = f"https://cf.shopee.com.br/file/{image}" if image else None

        return {
            "name": name,
            "price": price_float,
            "original_price": original_float,
            "url": url,
            "image_url": image_url,
            "source": DealSource.SHOPEE,
        }

    async def fetch_deals(self) -> list[dict[str, Any]]:
        if not (self._partner_id and self._partner_key):
            logger.warning("shopee credentials not configured, skipping")
            return []

        flash_sale_id = await self._get_active_flash_sale_id()
        if not flash_sale_id:
            logger.debug("no active shopee flash sale found")
            return []

        raw_items = await self._get_flash_sale_items(flash_sale_id)
        deals = [d for item in raw_items if (d := self._parse_item(item)) is not None]

        logger.bind(event="shopee_fetch", count=len(deals)).debug("shopee deals fetched")
        return deals

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "ShopeeClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()