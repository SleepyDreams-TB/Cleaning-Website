# ----------------- Paypal ----------------
from fastapi import APIRouter, HTTPException, Header, Depends
import os
from typing import cast
import httpx

from models import PayPalOrderRequest, PayPalCaptureRequest
from loki_logger import push_to_loki
from helpers import convert_currency
router = APIRouter()
demo_mode = True
BASE_URL = cast(str, os.getenv("BASE_URL"))

if demo_mode:
    paypal_username = cast(str, os.getenv("PAYPAL_SANDBOX_USERNAME"))
    paypal_password = cast(str, os.getenv("PAYPAL_SANDBOX_PASSWORD"))
    PAYPAL_TOKEN_URL = cast(str, os.getenv("PAYPAL_SANDBOX_TOKEN_URL"))
    PAYPAL_API_URL = cast(str, os.getenv("PAYPAL_SANDBOX_API_URL")) 
else:
    paypal_username = cast(str, os.getenv("PAYPAL_PROD_USERNAME"))
    paypal_password = cast(str, os.getenv("PAYPAL_PROD_PASSWORD"))
    PAYPAL_TOKEN_URL = cast(str, os.getenv("PAYPAL_PROD_TOKEN_URL"))
    PAYPAL_API_URL = cast(str, os.getenv("PAYPAL_PROD_API_URL"))

@router.post("/api/paypal-new")
async def new_payer_paypal_token():
    
    payload = {
        "grant_type": "client_credentials",
        "response_type": "id_token"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PAYPAL_TOKEN_URL,
                data=payload,
                auth=(paypal_username, paypal_password)
            )
            data = response.json()
            id_token = data["id_token"]
        
        return {"status": "success", "id_token": id_token,"response": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get paypal Auth Token: {e}")
    
@router.post("/api/paypal-exist/{customer_id}")
async def existing_payer_paypal_token(customer_id: str):
    
    payload = {
        "grant_type": "client_credentials",
        "response_type": "id_token",
        "target_customer_id": customer_id
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PAYPAL_API_URL,
                data=payload,
                auth=(paypal_username, paypal_password)
            )
            data = response.json()
            id_token = data["id_token"]
        
        return {"status": "success", "id_token": id_token,"response": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get paypal Auth Token: {e}")
    
# -------------------------Step 1:  Paypal Create Order Request --------------------
@router.post("/api/paypal/create-order")
async def create_order(request: PayPalOrderRequest):
    merchant_reference = request.merchant_reference
    zar_amount = request.amount
    
    try:
        amount_usd = await convert_currency(zar_amount, "ZAR", "USD")

        token_response = await new_payer_paypal_token()
        access_token = token_response['id_token']

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": "USD", "value": f"{amount_usd:.2f}"},
                "custom_id": merchant_reference
            }],
            "payment_source": {
                "paypal": {
                    "attributes": {
                        "vault": {
                            "store_in_vault": "ON_SUCCESS",
                            "usage_type": "MERCHANT"
                        }
                    },
                    "experience_context": {
                        "return_url": f"{BASE_URL}/redirects/paypal/paypal-redirect",
                        "cancel_url": f"{BASE_URL}/redirects/cancel"
                    }
                }
            }
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{PAYPAL_API_URL}/v2/checkout/orders",
                json=payload,
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            )
            
            if res.status_code != 200:
                await push_to_loki("paypal", "create_order_error", {
                    "merchant_reference": merchant_reference,
                    "amount": amount_usd,
                    "status_code": res.status_code,
                    "response": res.text
                })
                raise Exception(f"PayPal API returned {res.status_code}: {res.text}")
            
            data = res.json()

            approve_url = next((l["href"] for l in data.get("links", []) if l["rel"] == "payer-action"), None)

            if not approve_url:
                await push_to_loki("paypal", "create_order_error", {
                    "merchant_reference": merchant_reference,
                    "amount_usd": amount_usd,
                    "error": "No payer-action URL in response"
                })
                raise Exception("PayPal did not return a payer-action URL")
            
            await push_to_loki("paypal", "create_order_success", {
                "merchant_reference": merchant_reference,
                "amount_zar": zar_amount,
                "amount_usd": amount_usd,
                "paypal_order_id": data.get("id")
            })
        return {"approve_url": approve_url}
        
    except Exception as e:
        await push_to_loki("paypal", "create_order_exception", {
            "merchant_reference": merchant_reference,
            "zar_amount": zar_amount,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"PayPal API error: {str(e)}")
    
# -------------------------Step 2:  Paypal Capture Order Request --------------------

@router.post("/api/paypal/capture")
async def capture_order(request: PayPalCaptureRequest):
    order_id = request.order_id
    merchant_reference = request.merchant_reference
    
    try:
        token_response = await new_payer_paypal_token()
        access_token = token_response['id_token']

        payload = {}  # Capture doesn't need a body, just the order_id in the URL

        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{PAYPAL_API_URL}/v2/checkout/orders/{order_id}/capture",
                json=payload,
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            )
            
            if res.status_code not in (200, 201):
                await push_to_loki("paypal", "capture_order_error", {
                    "merchant_reference": merchant_reference,
                    "order_id": order_id,
                    "status_code": res.status_code,
                    "response": res.text
                })
                raise Exception(f"PayPal capture failed {res.status_code}: {res.text}")
            
            data = res.json()
            
            if data.get("status") == "COMPLETED":
                await push_to_loki("paypal", "capture_order_success", {
                    "merchant_reference": merchant_reference,
                    "order_id": order_id,
                    "paypal_status": data.get("status")
                })
                return {"status": "success", "order_id": order_id}
            else:
                await push_to_loki("paypal", "capture_order_incomplete", {
                    "merchant_reference": merchant_reference,
                    "order_id": order_id,
                    "paypal_status": data.get("status")
                })
                raise Exception(f"Payment status: {data.get('status')}")
        
    except Exception as e:
        await push_to_loki("paypal", "capture_order_exception", {
            "merchant_reference": merchant_reference,
            "order_id": order_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"PayPal capture error: {str(e)}")
