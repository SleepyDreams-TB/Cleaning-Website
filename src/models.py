from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSON
Base = declarative_base()

from pydantic import BaseModel
from typing import Optional, List, Dict
from pydantic import HttpUrl

# ==================== DATA MODELS ====================
# These define what data we expect when creating/updating products

class ProductCreate(BaseModel):
    """Fields required to create a new product"""
    name: str  # "Intel Core i5-12400F"
    slug: Optional[str] = None  # "intel-core-i5-12400f"
    short_description: Optional[str] = None  # "12th Gen 6-core CPU"
    description: str  # Full description
    price: float
    compare_at_price: Optional[float] = None
    currency: str = "ZAR"
    brand: Optional[str] = None
    sku: Optional[str] = None
    category: int  # category ID
    image_url: Optional[HttpUrl] = None  # Primary image
    images: Optional[List[HttpUrl]] = None  # Additional images
    stock_quantity: int = 0
    availability_status: str = "in_stock"  # in_stock | out_of_stock | preorder
    specifications: Optional[Dict[str, str]] = None  # structured specs
    weight_kg: Optional[float] = None
    is_active: bool = True
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class ProductUpdate(BaseModel):
    """Fields that can be updated (all optional)"""
    name: Optional[str] = None
    slug: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    compare_at_price: Optional[float] = None
    currency: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[int] = None
    image_url: Optional[HttpUrl] = None
    images: Optional[List[HttpUrl]] = None
    stock_quantity: Optional[int] = None
    availability_status: Optional[str] = None
    specifications: Optional[Dict[str, str]] = None
    weight_kg: Optional[float] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

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