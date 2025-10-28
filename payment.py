
from fastapi import APIRouter
router = APIRouter()

import random
import string
from datetime import datetime
from typing import Union
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pytz import UTC

from utils.dotenv_utils import dotenv
from callpayV2_Token import generate_callpay_token

CALLPAY_API_URL = dotenv.get("CALLPAY_API_URL")

# ------------------- Payment Endpoint -------------------
class PaymentRequest(BaseModel):
    payment_type: str
    amount: float
    merchant_reference: Union[str, None] = None

@router.post("/api/create-payment", include_in_schema=False)
async def create_payment(payment: PaymentRequest):
    callpay_creds = generate_callpay_token()
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    merchant_ref = payment.merchant_reference or f"PAY-{datetime.now(UTC).strftime('%y%m%d%H%M%S')}{suffix}"

    payload = {
        "amount": f"{payment.amount:.2f}",
        "merchant_reference": merchant_ref,
        "payment_type": payment.payment_type,
        "notify_url": "https://api.kingburger.site/webhook",
        "success_url": "https://kingburger.site/redirects/success",
        "error_url": "https://kingburger.site/redirects/error",
        "cancel_url": "https://kingburger.site/redirects/cancel"
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
            print("Callpay raw response:", text)
            try:
                data = response.json()
            except Exception:
                data = {"raw_response": text or "No content returned"}
            return data
    except Exception as e:
        print("Payment error:", e)
        raise HTTPException(status_code=500, detail=f"Payment request failed: {e}")
