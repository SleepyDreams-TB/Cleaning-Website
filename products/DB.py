from fastapi.responses import JSONResponse
from fastapi import Header, Depends, FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from pymongo import MongoClient
from typing import Union
from bson import ObjectId
from bson.errors import InvalidId

from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from passlib.hash import argon2

import ssl
import sys
import random
import string
import jwt
import json
from datetime import datetime, timedelta, timezone
import httpx
import os

from .callpayV2_Token import generate_callpay_token
from .orders import router as orders_router  # SQL-based orders router

# ------------------- Environment / Constants -------------------
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
CALLPAY_API_URL = os.getenv("CALLPAY_API_URL")
IP_WHITELIST = os.getenv("IP_WHITELIST", "54.72.191.28,54.194.139.201").split(",")

UTC = timezone.utc

# ------------------- FastAPI Lifespan -------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Python version:", sys.version)
    print("OpenSSL version:", ssl.OPENSSL_VERSION)
    yield

app = FastAPI(lifespan=lifespan, docs_url="/docs")
print("✅ FastAPI app loaded")

# ------------------- CORS -------------------
origins = [
    "https://kingburger.site",
    "https://cleaning-website-static-site.onrender.com",
    "http://127.0.0.1:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- MongoDB -------------------
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://SleepyDreams:saRqSb7xoc1cI1DO@kingburgercluster.ktvavv3.mongodb.net/?retryWrites=true&w=majority"
)
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client["cleaning_website"]
products_collection = db["products"]
users_collection = db["usersCleaningSite"]

# ------------------- Helpers -------------------
def check_user_avail(userName: str, email: str):
    try:
        user = users_collection.find_one({"$or": [{"userName": userName}, {"email": email}]})
        return user is not None
    except Exception as e:
        print(f"check_user_avail error: {e}")
        return False

def get_user_by_username(username: str):
    return users_collection.find_one({"userName": username})

def get_user_by_id(userID: str):
    try:
        return users_collection.find_one({"_id": ObjectId(userID)})
    except InvalidId:
        return None

def get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xrip = request.headers.get("x-real-ip")
    if xrip:
        return xrip.strip()
    return request.client.host if request.client else "unknown"

# ------------------- Logger -------------------
import logging
from pythonjsonlogger import jsonlogger

webhook_log_handler = logging.FileHandler("webhooks.log")
webhook_formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
webhook_log_handler.setFormatter(webhook_formatter)

webhook_logger = logging.getLogger("webhook_logger")
webhook_logger.addHandler(webhook_log_handler)
webhook_logger.setLevel(logging.INFO)

# ------------------- Password Generator -------------------
letters = list("abcdefghjklmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ")
numbers = list("23456789")
symbols = list("!#$%()*+")
cases = [0, 0, 1, 1, 2]

@app.post("/password/{length}")
async def generate_password(length: int):
    if length < 12 or length > 16:
        return {"error": "Length must be between 12 and 16"}
    password = ""
    for _ in range(length):
        case = random.choice(cases)
        if case == 0:
            password += random.choice(letters)
        elif case == 1:
            password += random.choice(numbers)
        else:
            password += random.choice(symbols)
    return {"password": password}

# ------------------- Registration -------------------
@app.post("/register/")
async def register(
    firstName: str = Form(...),
    lastName: str = Form(...),
    userName: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    cellNum: Union[str, None] = Form(None)
):
    try:
        if check_user_avail(userName, email):
            return JSONResponse(content={"error": "Username or email already exists"}, status_code=400)
        hashed_pw = argon2.hash(password)
        result = users_collection.insert_one({
            "firstName": firstName,
            "lastName": lastName,
            "userName": userName,
            "email": email,
            "password": hashed_pw,
            "cellNum": cellNum,
            "created_at": datetime.now(UTC)
        })
        if result.inserted_id:
            return JSONResponse(
                content={"message": "User created successfully", "id": str(result.inserted_id)},
                status_code=201
            )
        return JSONResponse(content={"error": "User insertion failed"}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": f"Server error: {str(e)}"}, status_code=500)

# ------------------- Basic Routes -------------------
@app.get("/")
def root():
    return {"message": "Welcome to the KingBurger API"}

@app.get("/health")
def health_check():
    return {"status": "alive"}

# ------------------- JWT Login -------------------
@app.post("/login/")
async def login(userName: str = Form(...), password: str = Form(...)):
    try:
        user = users_collection.find_one({"userName": userName})
        if not user:
            return JSONResponse(content={"error": "Invalid credentials"}, status_code=401)
        try:
            if not argon2.verify(password, user.get("password", "")):
                return JSONResponse(content={"error": "Invalid credentials"}, status_code=401)
        except Exception as e:
            print(f"Failed login for '{userName}': password verify error: {e}")
            return JSONResponse({"error": "Invalid credentials"}, status_code=401)
        
        payload = {
            "user_id": str(user["_id"]),
            "exp": datetime.now(UTC) + timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return JSONResponse({
            "message": "Login successful",
            "token": token,
            "user": {"firstName": user["firstName"]},
            "user_id": str(user["_id"])
        })
    except Exception as e:
        print("Login error:", e)
        return JSONResponse(content={"error": f"Server error: {e}"}, status_code=500)

@app.post("/logout/")
async def logout():
    return {"message": "Logout successful (client should discard the token)"}

# ------------------- Current User -------------------
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/dashboard")
async def dashboard(user=Depends(get_current_user)):
    return {"loggedIn_User": f"{user['firstName']}!"}

# ------------------- Payment Endpoint -------------------
class PaymentRequest(BaseModel):
    payment_type: str
    amount: float
    merchant_reference: Union[str, None] = None

@app.post("/api/create-payment", include_in_schema=False)
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
        "error_url": "https://kingburger.site/redirects/failure",
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

# ------------------- Webhook -------------------
@app.post("/webhook", include_in_schema=False)
async def webhook(request: Request):
    client_ip = get_client_ip(request)
    if client_ip not in IP_WHITELIST:
        webhook_logger.warning({
            "event": "forbidden_ip",
            "client_ip": client_ip
        })
        raise HTTPException(status_code=403, detail=f"Forbidden IP: {client_ip}")

    body_bytes = await request.body()
    try:
        payload = body_bytes.decode(errors="ignore")
    except Exception:
        payload = str(body_bytes)

    webhook_logger.info({
        "event": "webhook_received",
        "client_ip": client_ip,
        "payload": payload
    })
    return JSONResponse({"status": "ok", "client_ip": client_ip})

# ------------------- Include Orders Router (SQLAlchemy) -------------------
app.include_router(orders_router)

# ------------------- Run Server -------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
