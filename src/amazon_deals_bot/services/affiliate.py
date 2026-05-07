from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.utils.constants import DealSource
from amazon_deals_bot.utils.logger import logger


class AffiliateService:
    @staticmethod
    def build_link(url: str, source: str) -> str:
        normalized = source.upper()
        if normalized == DealSource.AMAZON:
            return AffiliateService._amazon(url)
        # Shopee and Magalu: the collector APIs return URLs that are already
        # affiliate-tagged when authenticated with affiliate credentials.
        if normalized in (DealSource.SHOPEE, DealSource.MAGALU):
            logger.bind(event="affiliate_passthrough", source=normalized).debug(
                "affiliate passthrough — url already tagged by source api"
            )
            return url
        return url

    @staticmethod
    def _amazon(url: str) -> str:
        # PA-API returns raw product URLs; the associate tag must be appended
        # so Amazon can attribute the sale to the affiliate account.
        if not settings.amazon_associate_tag:
            return url

        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params.pop("tag", None)
        params["tag"] = [settings.amazon_associate_tag]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))