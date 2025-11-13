
from fastapi import APIRouter
router = APIRouter()

import random
import string
from datetime import datetime, timezone
from typing import Union
import httpx
from fastapi import HTTPException
from pydantic import BaseModel
from datetime import UTC

from callpayV2_Token import generate_callpay_token
from dotenv import load_dotenv
import os

load_dotenv()

CALLPAY_API_URL = os.getenv("CALLPAY_API_URL")


# ------------------- Payment Endpoint -------------------
class PaymentRequest(BaseModel):
    payment_type: str
    amount: float
    merchant_reference: Union[str, None] = None

@router.post("/api/create-payment", include_in_schema=False)
async def create_payment(payment: PaymentRequest):
    callpay_creds = generate_callpay_token()
    merchant_ref = payment.merchant_reference
    payload = {
        "amount": f"{payment.amount:.2f}",
        "merchant_reference": merchant_ref,
        "payment_type": payment.payment_type,
        "notify_url": "https://api.kingburger.site/api/webhook",
        "success_url": "https://kingburger.site/api/redirects/success",
        "error_url": "https://kingburger.site/api/redirects/error",
        "cancel_url": "https://kingburger.site/api/redirects/cancel"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "auth-token": callpay_creds["Token"],
        "org-id": callpay_creds["org_id"],
        "timestamp": callpay_creds["timestamp"]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(CALLPAY_API_URL, data=payload, headers=headers)
            text = response.text
            try:
                data = response.json()
            except Exception:
                data = {"raw_response": text or "No content returned"}
        return {"status": "success", "response": data}
    except Exception as e:
        print("Payment error:", e)
        raise HTTPException(status_code=500, detail=f"Payment request failed: {e}")
