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

# ------------------- Configuration -------------------
IP_WHITELIST = [ip.strip() for ip in os.getenv("IP_WHITELIST", "").split(",") if ip.strip()]
router = APIRouter(tags=["webhook"])

#Grafana Loki configuration for pushing logs to Grafana Cloud
LOKI_URL = "https://sleepydreams.grafana.net/loki/api/v1/push"  
LOKI_USER = cast(str, os.getenv("LOKI_USER")) 
LOKI_KEY = cast(str, os.getenv("LOKI_KEY"))

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
        return "order_updated"
    except Exception as e:
        return (f"order_update_error: {str(e)}")

async def push_to_loki(event_type: str, payload: dict):  
    body = {  
        "streams": [{  
            "stream": {  
                "service": "psp-webhook",  
                "event_type": event_type  
            },  
            "values": [[  
                str(time.time_ns()),  
                json.dumps(payload)  
            ]]  
        }]  
    }  
    async with httpx.AsyncClient() as client:  
        await client.post(  
            LOKI_URL,  
            json=body,  
            auth=(LOKI_USER, LOKI_KEY)  
        )  


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


#@router.post("/webhook/test", include_in_schema=False)
#async def webhook_test(request: Request):
#    origin_ip = get_origin_ip(request)
#    log_event("info", "webhook_test_received", origin_ip=origin_ip)
#    return JSONResponse({"status": "ok"})