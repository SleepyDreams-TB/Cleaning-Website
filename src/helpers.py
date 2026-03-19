from fastapi import Request
from jose import jwt, JWTError
from datetime import datetime, timezone
import os
import random
import string
from fastapi import HTTPException
from typing import cast
import logging
import sys
import httpx
from pythonjsonlogger.jsonlogger import JsonFormatter
from pymongo import MongoClient
from loki_logger import push_to_loki

# Database setup (assuming MongoDB)
client = MongoClient(os.getenv("MONGODB_URI"))
db = client['kingburgerstore_db']
SECRET_KEY = cast(str, os.getenv("SECRET_KEY"))
ALGORITHM = cast(str, os.getenv("ALGORITHM", "HS256"))
APIVERVE_KEY = cast(str, os.getenv("APIVERVE_KEY"))

# ------------------- Helper: Generate Merchant Reference -------------------
def generate_merchant_reference():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return f"PAY-{timestamp}-{suffix}"


# ------------------- Helper: Extract User ID from JWT Token -------------------
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
    
# ------------------- Helper: Billing Info Helper -------------------
def billing_info_helper(current_user: dict) -> dict:
        return current_user.get("billing_info", {}).get("billing_address", {})

# ------------------- Helper: Currency Converter API -------------------
#
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert amount from one currency to another"""
    try:

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://v6.exchangerate-api.com/v6/076823edd4a018b50683afdf/latest/{from_currency}'
            )
            data = response.json()

            if data.get("result") == "error":
                await push_to_loki("currency_converter", "conversion_error", {
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "amount": amount,
                    "error": data.get('error-type')
                })
                raise Exception(f"API error: {data.get('error-type')}")

            rates = data.get("conversion_rates", {})
            converted_amount = amount * rates.get(to_currency, 1)

            await push_to_loki("currency_converter", "conversion_success", {
                "from_currency": from_currency,
                "to_currency": to_currency,
                "original_amount": amount,
                "converted_amount": converted_amount
            })
            
            return round(converted_amount, 2)
            
    except Exception as e:
        await push_to_loki("currency_converter", "conversion_error", {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "error": str(e)
        })
        raise Exception(f"Currency conversion failed: {e}")

# ------------------- Helper: Get Client IP from request -------------------
def get_origin_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xrip = request.headers.get("x-real-ip")
    if xrip:
        return xrip.strip()
    return request.client.host if request.client else "unknown"


# ------------ Logger -------------------
webhook_log_handler = logging.StreamHandler(sys.stdout)
webhook_formatter = JsonFormatter('%(asctime)s %(levelname)s %(message)s')
webhook_log_handler.setFormatter(webhook_formatter)

webhook_logger = logging.getLogger("webhook_logger")
webhook_logger.addHandler(webhook_log_handler)
webhook_logger.setLevel(logging.INFO)

# ------------------- Helper: Log Event -------------------
def log_event(level: str, event: str, **kwargs):
    log_data = {"event": event, **kwargs}
    if level == "info":
        webhook_logger.info(log_data)
    elif level == "warning":
        webhook_logger.warning(log_data)
    elif level == "error":
        webhook_logger.error(log_data)
