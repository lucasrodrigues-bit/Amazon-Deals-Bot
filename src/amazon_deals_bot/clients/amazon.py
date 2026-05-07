import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import httpx

from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.utils.constants import DealSource
from amazon_deals_bot.utils.logger import logger

_HOST = "webservices.amazon.com.br"
_REGION = "us-east-1"
_SERVICE = "ProductAdvertisingAPI"
_TARGET = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"
_PATH = "/paapi5/searchitems"
_ENDPOINT = f"https://{_HOST}{_PATH}"

_RESOURCES = [
    "Images.Primary.Large",
    "ItemInfo.Title",
    "Offers.Listings.Price",
    "Offers.Listings.SavingBasis",
]

# Top BR browse nodes to sweep for deals
_BROWSE_NODES = [
    "6291368011",   # Eletrônicos
    "16243390011",  # Informática
    "6764432011",   # Casa e Cozinha
    "18077270011",  # Ferramentas e Materiais de Construção
    "16318391011",  # Esportes e Aventura
    "17442412011",  # Beleza e Cuidados Pessoais
]

_MIN_DISCOUNT_PCT = 15
_ITEMS_PER_NODE = 10


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signing_key(secret_key: str, date_stamp: str) -> bytes:
    k_date = _hmac_sha256(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _hmac_sha256(k_date, _REGION)
    k_service = _hmac_sha256(k_region, _SERVICE)
    return _hmac_sha256(k_service, "aws4_request")


def _auth_headers(access_key: str, secret_key: str, payload: dict[str, Any]) -> dict[str, str]:
    now = datetime.now(tz=timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    body = json.dumps(payload, separators=(",", ":"))
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    # Headers sorted alphabetically (required by SigV4)
    headers_map = {
        "content-encoding": "amz-1.0",
        "content-type": "application/json; charset=utf-8",
        "host": _HOST,
        "x-amz-date": amz_date,
        "x-amz-target": _TARGET,
    }
    signed_headers = ";".join(sorted(headers_map))
    canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted(headers_map.items()))

    canonical_request = "\n".join([
        "POST", _PATH, "",
        canonical_headers, signed_headers, body_hash,
    ])

    credential_scope = f"{date_stamp}/{_REGION}/{_SERVICE}/aws4_request"
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, credential_scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    sig = hmac.new(
        _signing_key(secret_key, date_stamp),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    auth = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={sig}"
    )
    return {**headers_map, "Authorization": auth}


def _parse_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    items = data.get("SearchResult", {}).get("Items", [])
    results: list[dict[str, Any]] = []

    for item in items:
        name = item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue")
        url = item.get("DetailPageURL")
        image_url = (
            item.get("Images", {}).get("Primary", {}).get("Large", {}).get("URL")
        )

        listings = item.get("Offers", {}).get("Listings", [])
        if not listings:
            continue

        listing = listings[0]
        price_raw = listing.get("Price", {}).get("Amount")
        original_raw = listing.get("SavingBasis", {}).get("Amount")

        if not name or not url or price_raw is None:
            continue

        results.append({
            "name": name,
            "price": float(price_raw),
            "original_price": float(original_raw) if original_raw else None,
            "url": url,
            "image_url": image_url,
            "source": DealSource.AMAZON,
        })

    return results


class AmazonClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)
        self._access_key = settings.amazon_pa_api_access_key or ""
        self._secret_key = settings.amazon_pa_api_secret_key or ""
        self._partner_tag = settings.amazon_associate_tag or ""

    async def fetch_deals(self) -> list[dict[str, Any]]:
        if not (self._access_key and self._secret_key and self._partner_tag):
            logger.warning("amazon pa-api credentials not configured, skipping")
            return []

        all_deals: list[dict[str, Any]] = []

        for node_id in _BROWSE_NODES:
            payload: dict[str, Any] = {
                "BrowseNodeId": node_id,
                "PartnerTag": self._partner_tag,
                "PartnerType": "Associates",
                "Marketplace": settings.amazon_marketplace,
                "Resources": _RESOURCES,
                "ItemCount": _ITEMS_PER_NODE,
                "MinSavingPercent": _MIN_DISCOUNT_PCT,
            }

            headers = _auth_headers(self._access_key, self._secret_key, payload)

            try:
                response = await self._client.post(
                    _ENDPOINT,
                    content=json.dumps(payload, separators=(",", ":")),
                    headers=headers,
                )
                response.raise_for_status()
                items = _parse_items(response.json())
                all_deals.extend(items)
                logger.bind(event="amazon_fetch", node_id=node_id, count=len(items)).debug(
                    "amazon deals fetched"
                )
            except httpx.HTTPStatusError as exc:
                logger.warning(f"amazon pa-api error for node {node_id}: {exc.response.status_code}")
            except Exception as exc:
                logger.warning(f"amazon fetch failed for node {node_id}: {exc}")

        return all_deals

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AmazonClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()