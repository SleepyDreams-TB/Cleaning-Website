from fastapi import Request, HTTPException, APIRouter, Depends
from fastapi.responses import JSONResponse
import os
import logging
from pythonjsonlogger import jsonlogger
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# ------------------- Configuration -------------------
IP_WHITELIST = [ip.strip() for ip in os.getenv("IP_WHITELIST", "").split(",") if ip.strip()]
DATABASE_URL = os.getenv("DATABASE_URL")

router = APIRouter(tags=["webhook"])

# ------------------- Database Setup -------------------
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ------------------- Logger -------------------
webhook_log_handler = logging.FileHandler("webhooks.log")
webhook_formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
webhook_log_handler.setFormatter(webhook_formatter)

webhook_logger = logging.getLogger("webhook_logger")
webhook_logger.addHandler(webhook_log_handler)
webhook_logger.setLevel(logging.INFO)


# ------------------- Helper: Get Client IP from request -------------------
def get_client_ip(request: Request) -> str:
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


# ------------------- SQLAlchemy Models -------------------
class Order(Base):
    __tablename__ = 'orders'  # replace with your actual table name
    
    id = Column(Integer, primary_key=True)
    reference = Column(String, unique=True, nullable=False)  # ADDED: this was missing
    status = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def update_order_status(db, merchant_reference: str, status: str, reason: str = None):
    """Update order status in the database"""
    if not merchant_reference:
        webhook_logger.warning({
            "event": "invalid_reference",
            "reference": merchant_reference
        })
        return False
    
    try:
        order = db.query(Order).filter(Order.reference == merchant_reference).first()

        if order:
            order.status = status
            order.reason = reason
            order.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(order)
            webhook_logger.info({
                "event": "order_updated",
                "reference": merchant_reference,
                "status": status,
                "reason": reason
            })
            return True
        else:
            webhook_logger.warning({
                "event": "order_not_found",
                "reference": merchant_reference
            })
            return False
    except Exception as e:
        db.rollback()
        webhook_logger.error({
            "event": "order_update_error",
            "reference": merchant_reference,
            "error": str(e)
        })
        return False


# ------------------- Webhooks -------------------
@router.post("/webhook", include_in_schema=False)
async def webhook(request: Request, db=Depends(get_db)):
    client_ip = get_client_ip(request)
    
    # Validate IP whitelist
    if client_ip not in IP_WHITELIST:
        webhook_logger.warning({
            "event": "forbidden_ip",
            "client_ip": client_ip
        })
        raise HTTPException(status_code=403, detail="Forbidden")

    # Read request body
    try:
        body_bytes = await request.body()
        content_type = request.headers.get("content-type", "")
        
        # Try to parse as JSON
        payload_dict = None
        raw_payload = None
        
        if "application/json" in content_type:
            try:
                payload_dict = await request.json()
                webhook_logger.info({
                    "event": "webhook_received",
                    "client_ip": client_ip,
                    "payload": payload_dict
                })
            except Exception as json_error:
                # JSON parsing failed, fall back to raw
                raw_payload = body_bytes.decode(errors="ignore")
                webhook_logger.info({
                    "event": "webhook_received",
                    "client_ip": client_ip,
                    "payload": raw_payload,
                    "parse_error": str(json_error)
                })
        else:
            # Non-JSON content
            raw_payload = body_bytes.decode(errors="ignore")
            webhook_logger.info({
                "event": "webhook_received",
                "client_ip": client_ip,
                "payload": raw_payload
            })
        
        # If we have JSON payload with payment information, process it
        if payload_dict:
            merchant_reference = payload_dict.get("merchant_reference")
            status = payload_dict.get("status")
            reason = payload_dict.get("reason")
            success = payload_dict.get("success")
            
            # If payment-related fields are present, update the order
            if merchant_reference and status:
                update_success = update_order_status(db, merchant_reference, status, reason)
                
                if update_success:
                    webhook_logger.info({
                        "event": "payment_processed",
                        "client_ip": client_ip,
                        "status": status,
                        "success": success,
                        "merchant_reference": merchant_reference,
                        "reason": reason
                    })
        
        # Always return the same simple response
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        webhook_logger.error({
            "event": "webhook_error",
            "client_ip": client_ip,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")