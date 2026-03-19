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
import httpx, json, time
from loki_logger import push_to_loki

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


def update_order_status(db, merchant_reference: str, status: str, reason: str = None) -> str:
    """Update order status in the database."""
    if not merchant_reference:
        return "invalid_reference"

    order = db.query(Order).filter(Order.merchant_reference == merchant_reference).first()
    if not order:
        return "order_not_found"

    try:
        order.status = status
        order.reason = reason
        order.updated_at = datetime.now(timezone.utc)
        db.commit()
        return "order_updated"
    except Exception as e:
        db.rollback()
        return (f"order_update_error: {str(e)}")


@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request):
    origin_ip = get_origin_ip(request)

    if origin_ip not in IP_WHITELIST:
        log_event("warning", "forbidden_ip", origin_ip=origin_ip)
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        payload = await get_payload(request)
        log_event("info", "webhook_received", origin_ip=origin_ip, **payload)

        try:
            await push_to_loki("webhook_received", payload)
        except Exception as e:
            log_event("error", "loki_push_error", origin_ip=origin_ip, error=str(e))

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

# ------------------Paypal Webhook Endpoint --------------
@router.post("/webhook/paypal", include_in_schema=False)
async def paypal_webhook(request: Request):
    origin_ip = get_origin_ip(request)

    try:
        payload = await request.json()
        event_type = payload.get("event_type")
        resource = payload.get("resource", {})

        # Extract paypal_order_id from supplementary_data (for capture events)
        paypal_order_id = None
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            supplementary_data = resource.get("supplementary_data", {})
            related_ids = supplementary_data.get("related_ids", {})
            paypal_order_id = related_ids.get("order_id")
        elif event_type == "CHECKOUT.ORDER.COMPLETED":
            paypal_order_id = resource.get("id")

        await push_to_loki("paypal_webhook", "paypal_webhook_received", {
            "event_type": event_type,
            "paypal_order_id": paypal_order_id,
            "status": resource.get("status"),
            "origin_ip": origin_ip
        })

        # Handle CHECKOUT.ORDER.COMPLETED event
        if event_type == "CHECKOUT.ORDER.COMPLETED":
            status = resource.get("status")

            if paypal_order_id and status == "APPROVED":
                with db_session() as db:
                    order = db.query(Order).filter(Order.paypal_order_id == paypal_order_id).first()
                    if order:
                        order.status = "approved"
                        order.reason = "PayPal approved - awaiting capture"
                        order.updated_at = datetime.now(timezone.utc)
                        db.commit()

                        await push_to_loki("paypal_webhook", "paypal_order_approved", {
                            "paypal_order_id": paypal_order_id,
                            "status": status
                        })

                        log_event("info", "paypal_order_approved",
                            paypal_order_id=paypal_order_id,
                            status=status
                        )

        # Handle PAYMENT.CAPTURE.COMPLETED event
        elif event_type == "PAYMENT.CAPTURE.COMPLETED":
            status = resource.get("status")

            if status == "COMPLETED" and paypal_order_id:
                with db_session() as db:
                    order = db.query(Order).filter(Order.paypal_order_id == paypal_order_id).first()
                    if order:
                        order.status = "completed"
                        order.reason = "Payment captured successfully"
                        order.updated_at = datetime.now(timezone.utc)
                        db.commit()

                        await push_to_loki("paypal_webhook", "paypal_payment_captured", {
                            "paypal_order_id": paypal_order_id,
                            "status": status
                        })

                        log_event("info", "paypal_payment_captured",
                            paypal_order_id=paypal_order_id,
                            status=status
                        )

        # Handle payment failures
        elif event_type in ["PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.REFUNDED"]:
            reason = resource.get("status_details", {}).get("reason", "Unknown reason")

            if paypal_order_id:
                with db_session() as db:
                    order = db.query(Order).filter(Order.paypal_order_id == paypal_order_id).first()
                    if order:
                        order.status = "failed"
                        order.reason = f"PayPal: {event_type} - {reason}"
                        order.updated_at = datetime.now(timezone.utc)
                        db.commit()

                        await push_to_loki("paypal_webhook", "paypal_payment_failed", {
                            "paypal_order_id": paypal_order_id,
                            "event_type": event_type,
                            "reason": reason
                        })

                        log_event("error", "paypal_payment_failed",
                            paypal_order_id=paypal_order_id,
                            event_type=event_type,
                            reason=reason
                        )

        return JSONResponse({"status": "ok"})

    except Exception as e:
        await push_to_loki("paypal_webhook", "paypal_webhook_error", {
            "error": str(e),
            "origin_ip": origin_ip
        })
        log_event("error", "paypal_webhook_error", origin_ip=origin_ip, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")