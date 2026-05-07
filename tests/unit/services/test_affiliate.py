from unittest.mock import patch

from amazon_deals_bot.services.affiliate import AffiliateService
from amazon_deals_bot.utils.constants import DealSource


def test_amazon_appends_associate_tag():
    url = "https://www.amazon.com.br/dp/B09XYZ123"
    with patch(
        "amazon_deals_bot.services.affiliate.settings"
    ) as mock_settings:
        mock_settings.amazon_associate_tag = "meublog-20"
        result = AffiliateService.build_link(url, DealSource.AMAZON)

    assert "tag=meublog-20" in result
    assert result.startswith("https://www.amazon.com.br/dp/B09XYZ123")


def test_amazon_replaces_existing_tag():
    url = "https://www.amazon.com.br/dp/B09XYZ123?tag=old-tag-20"
    with patch(
        "amazon_deals_bot.services.affiliate.settings"
    ) as mock_settings:
        mock_settings.amazon_associate_tag = "novo-20"
        result = AffiliateService.build_link(url, DealSource.AMAZON)

    assert "tag=novo-20" in result
    assert "old-tag-20" not in result


def test_amazon_passthrough_when_no_tag_configured():
    url = "https://www.amazon.com.br/dp/B09XYZ123"
    with patch(
        "amazon_deals_bot.services.affiliate.settings"
    ) as mock_settings:
        mock_settings.amazon_associate_tag = None
        result = AffiliateService.build_link(url, DealSource.AMAZON)

    assert result == url


def test_shopee_passthrough():
    url = "https://shp.ee/abc123xyz"
    result = AffiliateService.build_link(url, DealSource.SHOPEE)
    assert result == url


def test_magalu_passthrough():
    url = "https://www.magazineluiza.com.br/produto/123456"
    result = AffiliateService.build_link(url, DealSource.MAGALU)
    assert result == url


def test_unknown_source_passthrough():
    url = "https://www.example.com/produto/99"
    result = AffiliateService.build_link(url, "MERCADOLIVRE")
    assert result == url