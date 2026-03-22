from fastapi import APIRouter, Request, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from models import Order, OrderItem
from sqlalchemy.orm import joinedload
from datetime import datetime
import os
from typing import cast
from postgresqlDB import db_session
from helpers_routers.helpers import get_current_user
from databaseConnections.mongoClient import get_collection
from bson import ObjectId

# --- Configuration ---
SECRET_KEY = cast(str, os.getenv("SECRET_KEY"))
ALGORITHM = cast(str, os.getenv("ALGORITHM", "HS256"))

# --- Router Setup ---
router = APIRouter(prefix="/api", tags=["orders"])

# --- Collections ---
products_collection = get_collection("products")

# --- Create Order ---
@router.post("/orders")
async def create_order(request: Request, authorization: str = Header(None)):
    """Create a new order from cart data."""
    user = get_current_user(authorization)
    user_id = str(user["_id"])

    data = await request.json()
    items = data.get("items", [])
    payment_type = data.get("payment_type", "unknown")
    delivery_info = data.get("delivery_info", {})
    merchant_reference = data.get("merchant_reference")

    if not items:
        raise HTTPException(status_code=400, detail="No items provided for order")
    if not delivery_info:
        raise HTTPException(status_code=400, detail="Delivery information is required")

    # ── Validate address type exists and belongs to this user ──
    address_type = delivery_info.get("type")
    if not address_type:
        raise HTTPException(status_code=400, detail="Address type is required")

    user_addresses = (
        user.get("billing_info", {})
            .get("billing_address", {})
    )

    if address_type not in user_addresses:
        raise HTTPException(
            status_code=403,
            detail="Invalid delivery address"
        )

    # ── Use server-side address data —
    verified_address = user_addresses[address_type]
    verified_delivery_info = {
        "type": address_type,
        "street": verified_address.get("street"),
        "city": verified_address.get("city"),
        "suburb": verified_address.get("suburb"),
        "postal_code": verified_address.get("postal_code"),
        "country": verified_address.get("country")
    }

    # ── Price Look up MongoDB —
    total = 0
    validated_items = []

    for item in items:
        try:
            product = products_collection.find_one({"_id": ObjectId(item["id"])})
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid product ID: {item.get('id')}")

        if not product:
            raise HTTPException(status_code=400, detail=f"Product not found: {item.get('id')}")

        quantity = int(item.get("quantity", 1))
        if quantity < 1 or quantity > 5:
            raise HTTPException(status_code=400, detail=f"Invalid quantity for {product['name']}")

        real_price = float(product["price"])
        total += real_price * quantity
        validated_items.append({
            "name": product["name"],
            "price": real_price,
            "quantity": quantity
        })

    # ── Write to PostgreSQL ──
    try:
        with db_session() as db:
            new_order = Order(
                merchant_reference=merchant_reference,
                user_id=user_id,
                total=round(total, 2),
                payment_type=payment_type,
                delivery_info=verified_delivery_info  # server-verified address
            )
            db.add(new_order)
            db.flush()

            for item in validated_items:
                order_item = OrderItem(
                    order_id=new_order.id,
                    name=item["name"],
                    price=item["price"],
                    quantity=item["quantity"]
                )
                db.add(order_item)

            return JSONResponse({
                "success": True,
                "merchant_reference": merchant_reference,
                "calculated_amount": round(total, 2),
                "status": new_order.status
            })

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
    """Retrieve paginated and filterable orders for the authenticated user."""
    user = get_current_user(authorization)
    user_id = str(user["_id"])

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
                "delivery_info": o.delivery_info,
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