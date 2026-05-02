import asyncio

from amazon_deals_bot.scheduler.setup import setup_scheduler


async def main():
    scheduler = setup_scheduler()
    scheduler.start()

    print("🚀 Bot rodando...")

    # mantém o loop vivo
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())