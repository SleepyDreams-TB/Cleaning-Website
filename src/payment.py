from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from jose import JWTError, jwt
import httpx
from callpayV2_Token import generate_callpay_token
from dotenv import load_dotenv
import os
from typing import cast
from pymongo import MongoClient

load_dotenv()
router = APIRouter()

CALLPAY_BASE_URL = "https://services.callpay.com/api/v2"
SECRET_KEY = cast(str, os.getenv("SECRET_KEY"))
ALGORITHM = cast(str, os.getenv("ALGORITHM", "HS256"))

MONGO_URI = cast(str, os.getenv("MONGO_URI"))
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client["kingburgerstore_db"]
users_collection = db["store_users"]

def get_callpay_headers() -> dict:
    creds = generate_callpay_token()
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "Auth-Token": creds["Token"],
        "Org-Id": creds["org_id"],
        "Timestamp": creds["timestamp"]
    }
#save guid as new field to mongodb where user_id match
def save_guid_to_db(user_id: str, guid: str, expiryDate: str = "", lastFour: str = ""):
    users_collection.update_one({"_id": user_id}, {"$set": {"guid": guid,
        "expiryDate": expiryDate,
        "lastFour":lastFour}})

    return (f"Saving GUID {guid} for customer {user_id} to the database")
# ------------------- EFT -------------------

class EFTPaymentRequest(BaseModel):
    amount: float
    merchant_reference: str
    customer_bank: str  # e.g. "absa", "fnb"

@router.post("/api/create-payment/eft")
async def create_eft_payment(payment: EFTPaymentRequest):
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

class CardDataset(BaseModel):
    cardNumber: str       # raw digits, no spaces
    expiryDate: str       # frontend sends MM/YY — we convert to MMYY
    cvv: str
    cardHolderName: str
    saveCardBool: bool
    user_id: str


class CreditCardPaymentRequest(BaseModel):
    amount: float
    merchant_reference: str
    cardDataset: CardDataset
    return_url: Optional[str]

def get_id_from_token(jwt_token) -> str:
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/api/create-payment/credit-card")
async def create_card_payment(payment: CreditCardPaymentRequest):
    card = payment.cardDataset

    # Convert MM/YY → MMYY as Callpay expects
    expiry = card.expiryDate.replace("/", "")

    payload = {
        "pan": card.cardNumber,
        "expiry": expiry,
        "cvv": card.cvv,
        "amount": f"{payment.amount:.2f}",
        "merchant_reference": payment.merchant_reference[:20],  # max 20 chars
        "first_name": card.cardHolderName.split()[0] if card.cardHolderName else "",
        "last_name": " ".join(card.cardHolderName.split()[1:]) if len(card.cardHolderName.split()) > 1 else "",
        "return_url": "https://kingburger.site/redirects/success",
        "notify_url": "https://api.kingburger.site/webhook"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CALLPAY_BASE_URL}/pay/direct",
                data=payload,
                headers=get_callpay_headers()
            )
            data = response.json()
        
        #Callpay returns { success, reason, callpay_transaction_id, merchant_reference, gateway_reference, gateway_response }

        return {"status": "success", "response": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Card payment failed: {e}")

# ------------------- Token (Saved Card) Payment -------------------

class TokenPaymentRequest(BaseModel):
    amount: float
    merchant_reference: str
    guid: str  # the customer's saved card GUID from Callpay

@router.post("/api/create-payment/saved-card")
async def create_token_payment(payment: TokenPaymentRequest):
    payload = {
        "amount": f"{payment.amount:.2f}",
        "reference": payment.merchant_reference[:32]  # max 32 chars per Callpay docs
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CALLPAY_BASE_URL}/customer-token/{payment.guid}/pay",
                data=payload,
                headers=get_callpay_headers()
            )
            data = response.json()

        # Response contains: success, amount, reason, callpay_transaction_id,
        # merchant_reference, gateway_reference, gateway_response
        return {"status": "success", "response": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token payment failed: {e}")

@router.post("/api/tokenize-card")
async def tokenize_card(merchant_reference : str, card: CardDataset):
    # Convert MM/YY → MMYY as Callpay expects

    payload = {
        "merchant_reference": merchant_reference,
        "pan": card.cardNumber,
        "expiry": card.expiryDate,
        "cvv": card.cvv
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CALLPAY_BASE_URL}/customer-token/direct",
                data=payload,
                headers=get_callpay_headers()
            )
            data = response.json()

        # Response contains: success, reason, guid, first_name, last_name
        if data.get("success"):
            save_guid_to_db(card.user_id, data["guid"], expiryDate=card.expiryDate, lastFour=card.cardNumber[-4:])
            return {"status": "success", "response": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Card tokenization failed: {e}")