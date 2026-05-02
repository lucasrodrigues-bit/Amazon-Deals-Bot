from apscheduler.schedulers.asyncio import AsyncIOScheduler

from amazon_deals_bot.scheduler.jobs import (
    run_collector,
    run_copywriter,
    run_publisher,
)


def setup_scheduler():
    scheduler = AsyncIOScheduler()

    # Fase 1 → a cada 15 min
    scheduler.add_job(run_collector, "interval", minutes=15)

    # Fase 2 → a cada 2 min
    scheduler.add_job(run_copywriter, "interval", minutes=2)

    # Fase 3 → a cada 1 min
    scheduler.add_job(run_publisher, "interval", minutes=1)

    return scheduler