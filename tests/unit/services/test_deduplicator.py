import hashlib

from amazon_deals_bot.services.deduplicator import DeduplicatorService


def test_normalize_url_strips_query_string():
    url = "https://www.amazon.com.br/dp/B09XYZ?ref=sr&tag=abc-20"
    assert DeduplicatorService.normalize_url(url) == "https://www.amazon.com.br/dp/B09XYZ"


def test_normalize_url_no_query_string():
    url = "https://www.amazon.com.br/dp/B09XYZ"
    assert DeduplicatorService.normalize_url(url) == url


def test_generate_deal_id_is_sha256():
    url = "https://www.amazon.com.br/dp/B09XYZ"
    price = 199.90
    expected = hashlib.sha256(f"{url}:{price}".encode()).hexdigest()
    assert DeduplicatorService.generate_deal_id(url, price) == expected


def test_generate_deal_id_same_url_different_price_yields_different_ids():
    url = "https://www.amazon.com.br/dp/B09XYZ"
    id1 = DeduplicatorService.generate_deal_id(url, 100.0)
    id2 = DeduplicatorService.generate_deal_id(url, 90.0)
    assert id1 != id2


def test_generate_deal_id_is_64_chars():
    deal_id = DeduplicatorService.generate_deal_id("https://example.com/product", 50.0)
    assert len(deal_id) == 64