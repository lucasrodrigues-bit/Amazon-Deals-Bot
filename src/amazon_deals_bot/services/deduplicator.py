import hashlib
from typing import Optional


class DeduplicatorService:
    @staticmethod
    def generate_deal_id(url: str, price: Optional[float]) -> str:
        """
        Gera um identificador único para o deal.

        Estratégia:
        - URL base (identidade do produto)
        - preço (detecta mudança de promoção)
        """
        raw = f"{url}:{price}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Remove parâmetros desnecessários da URL.

        (versão simples por enquanto)
        """
        return url.split("?")[0]