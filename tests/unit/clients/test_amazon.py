from unittest.mock import AsyncMock, patch

import pytest

from amazon_deals_bot.clients.amazon import AmazonClient, _auth_headers, _parse_items


def test_auth_headers_contains_required_keys():
    payload = {"test": "data"}
    headers = _auth_headers("fake_access", "fake_secret", payload)

    assert "Authorization" in headers
    assert "x-amz-date" in headers
    assert "x-amz-target" in headers
    assert "content-type" in headers
    assert "host" in headers


def test_auth_headers_authorization_format():
    headers = _auth_headers("AKIATEST", "supersecret", {"k": "v"})
    auth = headers["Authorization"]

    assert auth.startswith("AWS4-HMAC-SHA256 Credential=AKIATEST/")
    assert "SignedHeaders=" in auth
    assert "Signature=" in auth


def test_parse_items_extracts_fields():
    data = {
        "SearchResult": {
            "Items": [
                {
                    "DetailPageURL": "https://www.amazon.com.br/dp/B09XYZ",
                    "ItemInfo": {"Title": {"DisplayValue": "Fone de Ouvido XYZ"}},
                    "Images": {
                        "Primary": {"Large": {"URL": "https://images-na.amazon.com/img.jpg"}}
                    },
                    "Offers": {
                        "Listings": [
                            {
                                "Price": {"Amount": 149.90},
                                "SavingBasis": {"Amount": 299.90},
                            }
                        ]
                    },
                }
            ]
        }
    }

    items = _parse_items(data)

    assert len(items) == 1
    assert items[0]["name"] == "Fone de Ouvido XYZ"
    assert items[0]["price"] == 149.90
    assert items[0]["original_price"] == 299.90
    assert items[0]["url"] == "https://www.amazon.com.br/dp/B09XYZ"
    assert items[0]["image_url"] == "https://images-na.amazon.com/img.jpg"


def test_parse_items_skips_items_without_price():
    data = {
        "SearchResult": {
            "Items": [
                {
                    "DetailPageURL": "https://www.amazon.com.br/dp/B09",
                    "ItemInfo": {"Title": {"DisplayValue": "Produto Sem Preço"}},
                    "Offers": {"Listings": []},
                }
            ]
        }
    }

    items = _parse_items(data)
    assert len(items) == 0


def test_parse_items_handles_no_saving_basis():
    data = {
        "SearchResult": {
            "Items": [
                {
                    "DetailPageURL": "https://www.amazon.com.br/dp/B09",
                    "ItemInfo": {"Title": {"DisplayValue": "Produto"}},
                    "Images": {"Primary": {"Large": {"URL": None}}},
                    "Offers": {
                        "Listings": [
                            {"Price": {"Amount": 50.0}}
                        ]
                    },
                }
            ]
        }
    }

    items = _parse_items(data)
    assert len(items) == 1
    assert items[0]["original_price"] is None


async def test_fetch_deals_returns_empty_when_not_configured():
    with patch("amazon_deals_bot.clients.amazon.settings") as mock_settings:
        mock_settings.amazon_pa_api_access_key = None
        mock_settings.amazon_pa_api_secret_key = None
        mock_settings.amazon_associate_tag = None

        client = AmazonClient()
        result = await client.fetch_deals()
        await client.close()

    assert result == []


async def test_fetch_deals_handles_http_error():
    import httpx
    from unittest.mock import MagicMock

    with patch("amazon_deals_bot.clients.amazon.settings") as mock_settings:
        mock_settings.amazon_pa_api_access_key = "key"
        mock_settings.amazon_pa_api_secret_key = "secret"
        mock_settings.amazon_associate_tag = "tag-20"
        mock_settings.amazon_marketplace = "www.amazon.com.br"

        client = AmazonClient()
        client._access_key = "key"
        client._secret_key = "secret"
        client._partner_tag = "tag-20"

        # raise_for_status is synchronous in httpx
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "bad request", request=MagicMock(), response=mock_response
        )

        with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
            result = await client.fetch_deals()

        await client.close()

    assert result == []