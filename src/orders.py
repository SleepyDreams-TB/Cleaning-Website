from fastapi import APIRouter, Request, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from models import Order, OrderItem
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
from typing import cast
from postgresqlDB import db_session

# --- Configuration ---
SECRET_KEY = cast(str, os.getenv("SECRET_KEY"))
ALGORITHM = cast(str, os.getenv("ALGORITHM", "HS256"))

# --- Router Setup ---
router = APIRouter(prefix="/api", tags=["orders"])

# --- Helper Functions ---
from helpers import get_user_id_from_token, generate_merchant_reference

# --- Create Order ---
@router.post("/orders")
async def create_order(request: Request, authorization: str = Header(None)):
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
        with db_session() as db:
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

            response_data = {
            "message": "Order created successfully",
            "merchant_reference": merchant_reference,
            "total": total,
            "status": new_order.status
        }

        return JSONResponse(response_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")


# --- Get All Orders for the Logged-in User ---
@router.get("/orders/me")
def get_user_orders(
    authorization: str = Header(None),
    status: str | None = Query(None),
    payment_type: str | None = Query(None),
    merchant_reference: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """Retrieve pages and filterable orders for the authenticated user."""
    user_id = get_user_id_from_token(authorization)

    with db_session() as db:
        query = db.query(Order).options(joinedload(Order.items)).filter(Order.user_id == user_id)

        if status and status.strip():
            query = query.filter(Order.status.ilike(f"%{status.strip()}%"))
        if payment_type and payment_type.strip():
            query = query.filter(Order.payment_type.ilike(f"%{payment_type.strip()}%"))
        if merchant_reference and merchant_reference.strip():
            query = query.filter(Order.merchant_reference.ilike(f"%{merchant_reference.strip()}%"))

        if date_from and date_from.strip():
            try:
                date_from_dt = datetime.fromisoformat(date_from.strip())
                query = query.filter(Order.created_at >= date_from_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format")

        if date_to and date_to.strip():
            try:
                date_to_dt = datetime.fromisoformat(date_to.strip())
                query = query.filter(Order.created_at <= date_to_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format")

        total_records = query.count()
        orders = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        result = [
            {
                "merchant_reference": o.merchant_reference,
                "total": o.total,
                "payment_type": o.payment_type,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
                "items": [{"name": i.name, "price": i.price, "quantity": i.quantity} for i in o.items],
            }
            for o in orders
        ]

    return JSONResponse({
        "page": page,
        "page_size": page_size,
        "total_records": total_records,
        "total_pages": (total_records + page_size - 1) // page_size,
        "orders": result,
    })
