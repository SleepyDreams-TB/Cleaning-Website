from fastapi import Request, HTTPException, APIRouter, Depends
from fastapi.responses import JSONResponse
import sys
import os
import logging
from pythonjsonlogger.json import JsonFormatter
from datetime import datetime, timezone
from typing import cast
from urllib.parse import parse_qs
from models import Order
from helpers import get_origin_ip, log_event
from postgresqlDB import db_session
        
# ------------------- Configuration -------------------
IP_WHITELIST = [ip.strip() for ip in os.getenv("IP_WHITELIST", "").split(",") if ip.strip()]
router = APIRouter(tags=["webhook"])


#------------------- Helper: Parse Payload from urlencoded to JSON -------------------
async def get_payload(request: Request):
    if request.headers.get("content-type") == "application/x-www-form-urlencoded":
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8")
        parsed = parse_qs(body_str)
        return {k: v[0] for k, v in parsed.items()} # Extract the first value for each key from the parsed query parameters dictionary , parse_qs returns lists of values so the first value is always taken as only 1 is expected
    else:
        return await request.json()


def update_order_status(db, merchant_reference: str, status: str, reason: str = None) -> bool:
    """Update order status in the database."""
    if not merchant_reference:
        log_event("warning", "invalid_reference", reference=merchant_reference)
        return False

    order = db.query(Order).filter(Order.merchant_reference == merchant_reference).first()
    if not order:
        log_event("warning", "order_not_found", merchant_reference=merchant_reference)
        return False

    try:
        order.status = status
        order.reason = reason
        order.updated_at = datetime.now(timezone.utc)
        log_event("info", "order_updated", merchant_reference=merchant_reference, status=status, reason=reason)
        return True
    except Exception as e:
        log_event("error", "order_update_error", merchant_reference=merchant_reference, error=str(e))
        return False



@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request):
    origin_ip = get_origin_ip(request)

    if origin_ip not in IP_WHITELIST:
        log_event("warning", "forbidden_ip", origin_ip=origin_ip)
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        payload = await get_payload(request)
        log_event("info", "webhook_received", origin_ip=origin_ip, payload=payload)

        merchant_reference = payload.get("merchant_reference")
        status = payload.get("status")
        reason = payload.get("reason")

        if merchant_reference and status:
            with db_session() as db:
                success = update_order_status(db, merchant_reference, status, reason)
                log_event("info", "payment_processed", origin_ip=origin_ip, status=status, success=success, merchant_reference=merchant_reference, reason=reason)

        return JSONResponse({"status": "ok"})

    except Exception as e:
        log_event("error", "webhook_error", origin_ip=origin_ip, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
