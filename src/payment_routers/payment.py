from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from jose import JWTError, jwt
import httpx
from helpers_routers.callpayV2_Token import generate_callpay_token
from dotenv import load_dotenv
import os
from typing import cast
import logging
logger = logging.getLogger(__name__)
from helpers_routers.helpers import get_current_user
from models import CreditCardPaymentRequest, EFTPaymentRequest, TokenPaymentRequest, TokenizeCardDataset
from logs.loki_logger import push_to_loki


from bson import ObjectId

load_dotenv()
router = APIRouter()

CALLPAY_BASE_URL = cast(str, os.getenv("CALLPAY_BASE_URL"))
SECRET_KEY = cast(str, os.getenv("SECRET_KEY"))
ALGORITHM = cast(str, os.getenv("ALGORITHM", "HS256"))

from databaseConnections.mongoClient import get_collection
users_collection = get_collection("store_users")

def get_callpay_headers() -> dict:
    creds = generate_callpay_token()
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "Auth-Token": creds["Token"],
        "Org-Id": creds["org_id"],
        "Timestamp": creds["timestamp"]
    }

#save guid as new field to mongodb where user_id match
def save_guid_to_db(user_id: str, guid: str, expiryDate: str = "", lastFour: str = "", cardScheme = ""):
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "billing_info.hashed_card_data": {
                "guid": guid,
                "lastFour": lastFour,
                "expiryDate": expiryDate,
                "scheme": cardScheme
            }
        }}
    )

    return (f"Saving GUID {guid} for customer {user_id} to the database")


# ------------------- Helper: Get Card Details from Mongo -------------------  
@router.get("/api/get-card")
async def get_card_details(current_user = Depends(get_current_user)) -> dict:
    try:
        billing_info = current_user.get("billing_info", {})
        return billing_info.get("hashed_card_data", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get card details: {e}")

# ------------------- EFT -------------------

@router.post("/api/create-payment/eft")
async def create_eft_payment(payment: EFTPaymentRequest, current_user = Depends(get_current_user)):
    payload = {
        "payment_type": "eft",
        "amount": f"{payment.amount:.2f}",
        "merchant_reference": payment.merchant_reference,
        "customer_bank": payment.customer_bank,
        "notify_url": "https://api.kingburger.site/webhook",
        "success_url": "https://kingburger.site/redirects/success",
        "error_url": "https://kingburger.site/redirects/error",
        "cancel_url": "https://kingburger.site/redirects/cancel"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CALLPAY_BASE_URL}/payment-key",
                data=payload,
                headers=get_callpay_headers()
            )
            data = response.json()
        # Returns { key, url, origin } — frontend redirects to data["url"]
        return {"status": "success", "response": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"EFT payment setup failed: {e}")


# ------------------- Credit Card (Server to Server) -------------------
@router.post("/api/create-payment/credit-card")
async def create_card_payment(payment: CreditCardPaymentRequest, current_user = Depends(get_current_user)):
    card = payment.cardDataset
    
    # Convert MM/YY → MMYY as Callpay expects
    expiry = card.expiryDate.replace("/", "")

    payload = {
        "pan": card.cardNumber,
        "expiry": expiry,
        "cvv": card.cvv,
        "amount": f"{payment.amount:.2f}",
        "merchant_reference": payment.merchant_reference,
        "first_name": card.cardHolderName.split()[0] if card.cardHolderName else "",
        "last_name": " ".join(card.cardHolderName.split()[1:]) if len(card.cardHolderName.split()) > 1 else "",
        "notify_url": "https://api.kingburger.site/webhook",
        "return_url": "https://kingburger.site/redirects/return",
        "success_url": "https://kingburger.site/redirects/success",
        "error_url": "https://kingburger.site/redirects/error",
        "cancel_url": "https://kingburger.site/redirects/cancel"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CALLPAY_BASE_URL}/pay/direct",
                data=payload,
                headers=get_callpay_headers()
            )
            data = response.json()
        
        await push_to_loki("eft", "create_eft_payment_success", {
            "merchant_reference": payment.merchant_reference,
            "amount": payment.amount,
            "bank": payment.customer_bank
        })

        #Callpay returns { success, reason, callpay_transaction_id, merchant_reference, gateway_reference, gateway_response }

        return {"status": "success", "response": data}
    except Exception as e:
        await push_to_loki("eft", "create_eft_payment_error", {
            "merchant_reference": payment.merchant_reference,
            "amount": payment.amount,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Card payment failed: {e}")

# ------------------- Token (Saved Card) Payment -------------------

@router.post("/api/create-payment/saved-card")
async def create_token_payment(payment: TokenPaymentRequest, current_user = Depends(get_current_user)):
    payload = {
        "amount": f"{payment.amount:.2f}",
        "reference": payment.merchant_reference[:32],  # max 32 chars per Callpay docs
        "notify_url": "https://api.kingburger.site/webhook",
        "return_url": "https://kingburger.site/redirects/return",
        "success_url": "https://kingburger.site/redirects/success",
        "error_url": "https://kingburger.site/redirects/error",
        "cancel_url": "https://kingburger.site/redirects/cancel"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CALLPAY_BASE_URL}/customer-token/{payment.guid}/pay",
                data=payload,
                headers=get_callpay_headers()
            )
            data = response.json()

        await push_to_loki("credit_card", "create_card_payment_success", {
            "merchant_reference": payment.merchant_reference,
            "amount": payment.amount
        })

        # Response contains: success, amount, reason, callpay_transaction_id,
        # merchant_reference, gateway_reference, gateway_response
        return {"status": "success", "response": data}
    except Exception as e:
        await push_to_loki("saved_card", "create_token_payment_error", {
            "merchant_reference": payment.merchant_reference,
            "amount": payment.amount,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Token payment failed: {e}")

# ------------------- Tokenize Card endpoint to get guid -------------------

@router.post("/api/tokenize-card")
async def tokenize_card(card: TokenizeCardDataset, current_user = Depends(get_current_user)):
    expiry = card.expiryDate.replace("/", "")
    user_id = str(current_user["_id"])
    payload = {
        "merchant_reference": card.merchant_reference,
        "pan": card.cardNumber,
        "expiry": expiry,
        "cvv": card.cvv,
        "notify_url": "https://api.kingburger.site/webhook",
        "success_url": "https://kingburger.site/redirects/success",
        "error_url": "https://kingburger.site/redirects/error",
        "cancel_url": "https://kingburger.site/redirects/cancel"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CALLPAY_BASE_URL}/customer-token/direct",
                data=payload,
                headers=get_callpay_headers()
            )
            data = response.json()
        if data.get("guid"):
            save_guid_to_db(user_id, data["guid"], expiryDate=card.expiryDate, lastFour=card.cardNumber[-4:], cardScheme = card.cardScheme)
            await push_to_loki("tokenize", "tokenize_card_success", {
                "merchant_reference": card.merchant_reference,
                "user_id": user_id
            })
            return {"status": "success", "response": data}
        else:
            return {"status": "failed", "response": data}
    except Exception as e:
        await push_to_loki("tokenize", "tokenize_card_error", {
            "merchant_reference": card.merchant_reference,
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Card tokenization failed: {e}")