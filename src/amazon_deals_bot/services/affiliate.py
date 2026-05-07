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
        if normalized == DealSource.SHOPEE:
            return AffiliateService._shopee(url)
        if normalized == DealSource.MAGALU:
            return AffiliateService._magalu(url)
        return url

    @staticmethod
    def _amazon(url: str) -> str:
        if not settings.amazon_associate_tag:
            return url

        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params.pop("tag", None)
        params["tag"] = [settings.amazon_associate_tag]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    @staticmethod
    def _shopee(url: str) -> str:
        if not settings.shopee_app_id:
            return url

        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        params["aff_id"] = [settings.shopee_app_id]
        new_query = urlencode(params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    @staticmethod
    def _magalu(url: str) -> str:
        logger.bind(event="affiliate_passthrough", source=DealSource.MAGALU).debug(
            "magalu affiliate passthrough"
        )
        return url