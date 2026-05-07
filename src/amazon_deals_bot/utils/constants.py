from enum import Enum


class DealStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    SENT = "SENT"
    FAILED = "FAILED"


class DealSource(str, Enum):
    AMAZON = "AMAZON"
    SHOPEE = "SHOPEE"
    MAGALU = "MAGALU"