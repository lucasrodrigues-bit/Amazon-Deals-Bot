import httpx
import sqlalchemy.exc
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
    retry_if_exception_type,
    before_log,
)
from amazon_deals_bot.utils.logger import logger

retry_api = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    before=before_log(logger, "WARNING"),
    reraise=True,
)

retry_db = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(sqlalchemy.exc.OperationalError),
    before=before_log(logger, "WARNING"),
    reraise=True,
)