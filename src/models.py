from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSON
Base = declarative_base()

# --- SQLAlchemy Models ---
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    merchant_reference = Column(String(50), unique=True, nullable=False)
    user_id = Column(String(24), nullable=False)
    total = Column(Float, nullable=False)
    payment_type = Column(String(50), nullable=False)
    delivery_info = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    reason = Column(String(255), nullable=True)
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")