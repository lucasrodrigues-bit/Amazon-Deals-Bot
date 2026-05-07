from amazon_deals_bot.db.session import AsyncSessionLocal
from amazon_deals_bot.services.collector import CollectorService
from amazon_deals_bot.services.copywriter import CopywriterService
from amazon_deals_bot.services.publisher import PublisherService
from amazon_deals_bot.utils.logger import logger


async def run_collector() -> None:
    async with AsyncSessionLocal() as session:
        service = CollectorService(session)
        count = await service.run()
        logger.bind(event="collector_job", new_deals=count).info("collector job finished")


async def run_copywriter() -> None:
    async with AsyncSessionLocal() as session:
        service = CopywriterService(session)
        count = await service.process()
        logger.bind(event="copywriter_job", processed=count).info("copywriter job finished")


async def run_publisher() -> None:
    async with AsyncSessionLocal() as session:
        service = PublisherService(session)
        count = await service.process()
        logger.bind(event="publisher_job", sent=count).info("publisher job finished")