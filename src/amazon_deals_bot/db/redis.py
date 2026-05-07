import redis.asyncio as aioredis
from amazon_deals_bot.config.settings import settings

redis_client: aioredis.Redis = aioredis.from_url(settings.redis_url, decode_responses=True)