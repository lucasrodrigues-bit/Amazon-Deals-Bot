from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Text,
    DateTime,
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Deal(Base):
    __tablename__ = "deals"

    id = Column(String, primary_key=True)  # hash do produto

    name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2))
    original_price = Column(Numeric(10, 2))

    url = Column(Text)
    affiliate_url = Column(Text)

    image_url = Column(Text)

    source = Column(String(50))  # amazon | shopee | magalu

    discount_pct = Column(Integer)

    status = Column(String(50), default="PENDING")
    # PENDING | READY | SENT | FAILED

    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)