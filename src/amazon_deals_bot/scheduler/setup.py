from apscheduler.schedulers.asyncio import AsyncIOScheduler

from amazon_deals_bot.config.settings import settings
from amazon_deals_bot.scheduler.jobs import (
    run_collector,
    run_copywriter,
    run_publisher,
)


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        run_collector,
        "interval",
        minutes=settings.phase1_interval_minutes,
        id="collector",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_copywriter,
        "interval",
        seconds=settings.copywriter_interval_seconds,
        id="copywriter",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_publisher,
        "interval",
        seconds=settings.phase2_interval_seconds,
        id="publisher",
        max_instances=1,
        coalesce=True,
    )

    return scheduler