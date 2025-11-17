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

from models import Order

# --- Database Setup ---
from postgresqlDB import SessionLocal

# ------------------- Configuration -------------------
IP_WHITELIST = [ip.strip() for ip in os.getenv("IP_WHITELIST", "").split(",") if ip.strip()]
router = APIRouter(tags=["webhook"])

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
    db = SessionLocal()
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
    try:
        payload = await request.json()
    except Exception as e:
        webhook_logger.error({"event": "invalid_json", "error": str(e)})
        raise HTTPException(status_code=400, detail="Invalid JSON")

    webhook_logger.info({
        "event": "webhook_received",
        "origin_ip": origin_ip,
        "payload": payload,
        "headers": dict(request.headers)
    })

    if origin_ip not in IP_WHITELIST:
        webhook_logger.warning({"event": "forbidden_ip", "origin_ip": origin_ip})
        raise HTTPException(status_code=403, detail="Forbidden")

    merchant_reference = payload.get("merchant_reference")
    status = payload.get("status")
    reason = payload.get("reason", "N/A")  # default to "N/A" if successful

    if not merchant_reference or not status:
        webhook_logger.warning({"event": "missing_fields", "payload": payload})
        raise HTTPException(status_code=400, detail="Missing merchant_reference or status")

    try:
        updated = update_order_status(db, merchant_reference, status, reason)
        if not updated:
            webhook_logger.warning({"event": "update_failed", "merchant_reference": merchant_reference})
    except Exception as e:
        webhook_logger.error({"event": "webhook_processing_error", "error": str(e)})
        raise HTTPException(status_code=500, detail="Internal server error")

    return JSONResponse({"status": "ok"})

