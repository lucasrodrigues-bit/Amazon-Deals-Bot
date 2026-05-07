from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_session():
    """AsyncSession simulada para testes unitários de services/repositories."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_redis():
    """Redis client simulado para testes que dependem de rate limiting."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_openai_response():
    """Resposta simulada da OpenAI para testes do copywriter."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "🔥 Produto incrível! De R$199 por R$99. Só hoje: https://amzn.to/teste"
    response.usage = MagicMock()
    response.usage.prompt_tokens = 150
    response.usage.completion_tokens = 50
    return response


@pytest.fixture
def sample_deal_data():
    """Dados de produto de exemplo para testes."""
    return {
        "name": "Fone de Ouvido Bluetooth XYZ Pro",
        "price": 149.90,
        "original_price": 299.90,
        "url": "https://www.amazon.com.br/dp/B09XYZ123",
        "image_url": "https://images-na.ssl-images-amazon.com/images/I/test.jpg",
        "source": "AMAZON",
    }