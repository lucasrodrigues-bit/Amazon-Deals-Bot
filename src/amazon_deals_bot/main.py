import asyncio
import signal

from amazon_deals_bot.scheduler.setup import setup_scheduler
from amazon_deals_bot.utils.logger import logger


async def main() -> None:
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("bot started")

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_shutdown() -> None:
        logger.info("shutdown signal received, stopping gracefully...")
        scheduler.shutdown(wait=False)
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_shutdown)

    await stop_event.wait()
    logger.info("bot stopped cleanly")


if __name__ == "__main__":
    asyncio.run(main())