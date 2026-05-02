from amazon_deals_bot.db.session import AsyncSessionLocal
from amazon_deals_bot.services.collector import CollectorService
from amazon_deals_bot.services.copywriter import CopywriterService
from amazon_deals_bot.services.publisher import PublisherService


# 🔹 FASE 1 — COLETA (por enquanto mock)
async def run_collector():
    async with AsyncSessionLocal() as session:
        service = CollectorService(session)

        # MOCK TEMPORÁRIO
        await service.process_product(
            name="Produto Teste",
            price=99.90,
            original_price=199.90,
            url="https://amazon.com/teste",
            image_url=None,
            source="amazon",
        )


# 🔹 FASE 2 — COPY
async def run_copywriter():
    async with AsyncSessionLocal() as session:
        service = CopywriterService(session)
        await service.process()


# 🔹 FASE 3 — ENVIO
async def run_publisher():
    async with AsyncSessionLocal() as session:
        service = PublisherService(session)
        await service.process()