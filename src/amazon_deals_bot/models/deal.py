from sqlalchemy import Column, String, Integer, Numeric, Text, DateTime
from datetime import datetime

from amazon_deals_bot.db.session import Base


class Deal(Base):
    __tablename__ = "deals"

    # ID = hash (deduplicação)
    id = Column(String, primary_key=True)

    # Dados do produto
    name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    original_price = Column(Numeric(10, 2), nullable=True)
    discount_pct = Column(Integer, nullable=True)

    # Links
    url = Column(Text, nullable=False)
    affiliate_url = Column(Text, nullable=True)

    # Imagem
    image_url = Column(Text, nullable=True)

    # Origem
    source = Column(String(50), nullable=False)

    # Pipeline
    status = Column(String(50), nullable=False, default="PENDING")

    # Retry
    retry_count = Column(Integer, default=0)

    # Copy
    copy = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)