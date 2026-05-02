from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from amazon_deals_bot.config.settings import settings

# Base para os models
Base = declarative_base()

# Engine async (PostgreSQL + asyncpg)
engine = create_async_engine(
    settings.database_url,
    echo=False,  # mudar para True se quiser debug SQL
    pool_pre_ping=True,
)

# Factory de sessões
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependency/helper para uso futuro
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session