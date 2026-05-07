import sys
from loguru import logger
from amazon_deals_bot.config.settings import settings

logger.remove()

if settings.environment == "production":
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
            '"level":"{level}",'
            '"message":"{message}",'
            '"extra":{extra}}}'
        ),
        serialize=False,
        colorize=False,
    )
else:
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )