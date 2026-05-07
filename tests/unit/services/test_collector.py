from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amazon_deals_bot.services.collector import CollectorService
from amazon_deals_bot.utils.constants import DealSource


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def collector(mock_session):
    svc = CollectorService(mock_session)
    svc.repo = AsyncMock()
    return svc


async def test_process_product_skips_duplicate(collector):
    collector.repo.exists.return_value = True

    result = await collector.process_product(
        name="Produto Teste",
        price=99.90,
        original_price=199.90,
        url="https://www.amazon.com.br/dp/B09XYZ",
        image_url=None,
        source=DealSource.AMAZON,
    )

    assert result is None
    collector.repo.create.assert_not_called()


async def test_process_product_creates_new_deal(collector):
    collector.repo.exists.return_value = False
    collector.repo.create.return_value = None

    result = await collector.process_product(
        name="Produto Teste",
        price=99.90,
        original_price=199.90,
        url="https://www.amazon.com.br/dp/B09XYZ",
        image_url="https://images.amazon.com/img.jpg",
        source=DealSource.AMAZON,
    )

    assert result is not None
    assert result.name == "Produto Teste"
    assert result.price == 99.90
    assert result.discount_pct == 50
    assert result.status == "PENDING"
    collector.repo.create.assert_called_once()


async def test_process_product_calculates_discount(collector):
    collector.repo.exists.return_value = False
    collector.repo.create.return_value = None

    result = await collector.process_product(
        name="Produto",
        price=75.0,
        original_price=100.0,
        url="https://www.amazon.com.br/dp/ABC",
        image_url=None,
        source=DealSource.AMAZON,
    )

    assert result is not None
    assert result.discount_pct == 25


async def test_process_product_no_original_price(collector):
    collector.repo.exists.return_value = False
    collector.repo.create.return_value = None

    result = await collector.process_product(
        name="Produto",
        price=50.0,
        original_price=None,
        url="https://www.amazon.com.br/dp/ABC",
        image_url=None,
        source=DealSource.AMAZON,
    )

    assert result is not None
    assert result.discount_pct is None


async def test_process_product_normalizes_url(collector):
    collector.repo.exists.return_value = False
    collector.repo.create.return_value = None

    await collector.process_product(
        name="Produto",
        price=50.0,
        original_price=100.0,
        url="https://www.amazon.com.br/dp/ABC?ref=sr_1_1&tag=old-20",
        image_url=None,
        source=DealSource.AMAZON,
    )

    created_deal = collector.repo.create.call_args[0][0]
    assert "?" not in created_deal.url


async def test_run_skips_amazon_when_not_configured(collector):
    with patch("amazon_deals_bot.services.collector.settings") as mock_settings:
        mock_settings.amazon_pa_api_access_key = None
        mock_settings.shopee_app_id = None
        mock_settings.shopee_secret = None
        mock_settings.magalu_token = None

        total = await collector.run()

    assert total == 0


async def test_run_counts_new_deals(collector):
    collector.repo.exists.return_value = False
    collector.repo.create.return_value = None

    fake_product = {
        "name": "Produto X",
        "price": 49.90,
        "original_price": 99.90,
        "url": "https://www.amazon.com.br/dp/B09",
        "image_url": None,
        "source": DealSource.AMAZON,
    }

    mock_amazon_client = AsyncMock()
    mock_amazon_client.fetch_deals.return_value = [fake_product, fake_product]
    mock_amazon_client.__aenter__ = AsyncMock(return_value=mock_amazon_client)
    mock_amazon_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("amazon_deals_bot.services.collector.settings") as mock_settings,
        patch("amazon_deals_bot.services.collector.AmazonClient", return_value=mock_amazon_client),
    ):
        mock_settings.amazon_pa_api_access_key = "fake_key"
        mock_settings.shopee_app_id = None
        mock_settings.shopee_secret = None
        mock_settings.magalu_token = None

        # Second call to exists returns True (duplicate)
        collector.repo.exists.side_effect = [False, True]

        total = await collector.run()

    assert total == 1