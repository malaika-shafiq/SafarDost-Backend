import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from database import Base


def get_utc_now():
    """
    Standardized UTC Timestamp Helper: Generates precise timezone-naive
    datetime stamps optimized for storage engines like SQLite and PostgreSQL.
    """
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class GearItem(Base):
    __tablename__ = "gear_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)  # High-speed index lookup anchor for case-insensitive searches
    description = Column(String, nullable=False)
    price_pkr = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)


class GearOrder(Base):
    __tablename__ = "gear_orders"

    id = Column(Integer, primary_key=True, index=True)

    # 🔒 Relational Integrity Fences: Locks transaction ledgers permanently to system user identities
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gear_item_id = Column(Integer, ForeignKey("gear_items.id"), nullable=False)

    purchase_quantity = Column(Integer, nullable=False)
    total_invoice_pkr = Column(Float, nullable=False)
    created_at = Column(DateTime, default=get_utc_now)
