from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
from jose import jwt, JWTError
from datetime import datetime, timezone
import os
import random
import string

# --- Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

router = APIRouter(prefix="/api", tags=["orders"])

# --- SQLAlchemy Models ---
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    merchant_reference = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)
    payment_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(String(50), default="pending")

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")


Base.metadata.create_all(bind=engine)


# --- Helper Functions ---
def generate_merchant_reference():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"PAY-{timestamp}-{suffix}"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id_from_token(authorization: str):
    """Extract user_id from Bearer JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# --- Create Order ---
@router.post("/orders")
async def create_order(request: Request, authorization: str = Header(None), db=Depends(get_db)):
    """Create a new order from cart data."""
    user_id = get_user_id_from_token(authorization)

    data = await request.json()
    items = data.get("items", [])
    payment_type = data.get("payment_type", "unknown")

    if not items:
        raise HTTPException(status_code=400, detail="No items provided for order")

    total = sum(item["price"] * item["quantity"] for item in items)
    merchant_reference = generate_merchant_reference()

    try:
        new_order = Order(
            merchant_reference=merchant_reference,
            user_id=user_id,
            total=total,
            payment_type=payment_type
        )
        db.add(new_order)
        db.flush()

        for item in items:
            order_item = OrderItem(
                order_id=new_order.id,
                name=item["name"],
                price=item["price"],
                quantity=item["quantity"]
            )
            db.add(order_item)

        db.commit()
        db.refresh(new_order)

        return JSONResponse({
            "message": "Order created successfully",
            "merchant_reference": merchant_reference,
            "total": total,
            "status": new_order.status
        })
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")


# --- Get All Orders for the Logged-in User ---
@router.get("/orders/me")
def get_user_orders(authorization: str = Header(None), db=Depends(get_db)):
    """Retrieve all orders for the currently authenticated user."""
    user_id = get_user_id_from_token(authorization)

    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    if not orders:
        return JSONResponse({"message": "No orders found for this user."})

    result = []
    for order in orders:
        result.append({
            "merchant_reference": order.merchant_reference,
            "total": order.total,
            "payment_type": order.payment_type,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "items": [
                {"name": i.name, "price": i.price, "quantity": i.quantity}
                for i in order.items
            ]
        })

    return JSONResponse(result)
