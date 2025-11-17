from fastapi import Request, HTTPException, APIRouter, Depends
from fastapi.responses import JSONResponse
import sys
import os
import logging
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import cast

from models import Base, Order

# ------------------- Configuration -------------------
IP_WHITELIST = [ip.strip() for ip in os.getenv("IP_WHITELIST", "").split(",") if ip.strip()]
DATABASE_URL = cast(str, os.getenv("DATABASE_URL"))

router = APIRouter(tags=["webhook"])

# ------------------- Database Setup -------------------
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ------------ Logger -------------------
webhook_log_handler = logging.StreamHandler(sys.stdout)
webhook_formatter = JsonFormatter('%(asctime)s %(levelname)s %(message)s')
webhook_log_handler.setFormatter(webhook_formatter)

webhook_logger = logging.getLogger("webhook_logger")
webhook_logger.addHandler(webhook_log_handler)
webhook_logger.setLevel(logging.INFO)


# ------------------- Helper: Get Client IP from request -------------------
def get_origin_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xrip = request.headers.get("x-real-ip")
    if xrip:
        return xrip.strip()
    return request.client.host if request.client else "unknown"


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

def update_order_status(db, merchant_reference: str, status: str, reason: str) -> bool:
    """Update order status in the database"""
    if not merchant_reference:
        webhook_logger.warning({
            "event": "invalid_reference",
            "reference": merchant_reference
        })
        return False
    
    try:
        order = db.query(Order).filter(Order.merchant_reference == merchant_reference).first()

        if order:
            order.status = status
            order.reason = reason
            order.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(order)
            webhook_logger.info({
                "event": "order_updated",
                "merchant_reference": merchant_reference,
                "status": status,
                "reason": reason
            })
            return True
        else:
            webhook_logger.warning({
                "event": "order_not_found",
                "merchant_reference": merchant_reference
            })
            return False
    except Exception as e:
        db.rollback()
        webhook_logger.error({
            "event": "order_update_error",
            "merchant_reference": merchant_reference,
            "error": str(e)
        })
        return False


@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request, db=Depends(get_db)):
    origin_ip = get_origin_ip(request)

    if origin_ip not in IP_WHITELIST:
        webhook_logger.warning({"event": "forbidden_ip", "origin_ip": origin_ip})
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        payload = await request.json()
        webhook_logger.info({"event": "webhook_received", "origin_ip": origin_ip, "payload": payload})

        merchant_reference = payload.get("merchant_reference")
        status = payload.get("status")
        reason = payload.get("reason")

        if merchant_reference and status:
            update_order_status(db, merchant_reference, status, reason)
            webhook_logger.info({
                "event": "payment_processed",
                "origin_ip": origin_ip,
                "status": status,
                "success": payload.get("success"),
                "merchant_reference": merchant_reference,
                "reason": reason
            })

        return JSONResponse({"status": "ok"})

    except Exception as e:
        webhook_logger.error({"event": "webhook_error", "origin_ip": origin_ip, "error": str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")
