from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # DATABASE
    database_url: str
    database_sync_url: str

    # REDIS
    redis_url: str

    # AMAZON
    amazon_pa_api_access_key: Optional[str] = None
    amazon_pa_api_secret_key: Optional[str] = None
    amazon_associate_tag: Optional[str] = None
    amazon_marketplace: str = "www.amazon.com.br"

    # SHOPEE
    shopee_app_id: Optional[str] = None
    shopee_secret: Optional[str] = None

    # MAGALU
    magalu_token: Optional[str] = None

    # OPENAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 200
    openai_temperature: float = 0.8

    # WHATSAPP
    evolution_api_url: str
    evolution_api_key: str
    evolution_instance_name: str

    # TELEGRAM
    telegram_bot_token: Optional[str] = None
    telegram_channel_id: Optional[str] = None

    # ALERTAS
    alert_telegram_bot_token: Optional[str] = None
    alert_telegram_chat_id: Optional[str] = None

    # SCHEDULER
    phase1_interval_minutes: int = 15
    phase2_interval_seconds: int = 60

    # ENV
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()