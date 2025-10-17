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
from datetime import datetime, timedelta, UTC
import httpx

from .callpayV2_Token import generate_callpay_token

# --------- Helper constants ---------

SECRET_KEY = "hCZ*9R9E2v37Dq(%"
ALGORITHM = "HS256"
CALLPAY_API_URL = "https://services.callpay.com/api/v2/payment-key"
# Only allow these IPs
IP_WHITELIST = {"54.72.191.28", "54.194.139.201"}

# --------- FastAPI lifespan ---------
@asynccontextmanager
async def lifespan(app: FastAPI,):
    print("Python version:", sys.version)
    print("OpenSSL version:", ssl.OPENSSL_VERSION)
    yield

app = FastAPI(lifespan=lifespan, docs_url="/docs")
print("✅ FastAPI app loaded")


# --------- CORS middleware ---------
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





# --------- MongoDB setup ---------
client = MongoClient(
    "mongodb+srv://SleepyDreams:saRqSb7xoc1cI1DO@kingburgercluster.ktvavv3.mongodb.net/?retryWrites=true&w=majority",
    tls=True,
    tlsAllowInvalidCertificates=False
)
db = client["cleaning_website"]
products = db["products"]
usersCleaningSite = db["usersCleaningSite"]



# --------- Helper functions ---------
def check_user_avail(userName: str, email: str):
    try:
        user = usersCleaningSite.find_one({"$or": [{"userName": userName}, {"email": email}]})
        return user is not None
    except Exception:
        return False

def get_user_by_username(username: str):
    return usersCleaningSite.find_one({"userName": username})

def get_user_by_id(userID: str):
    try:
        return usersCleaningSite.find_one({"_id": ObjectId(userID)})
    except InvalidId:
        return None

def get_client_ip(request: Request) -> str:
    """
    Extract client IP from headers or fallback to peer IP.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Take the first IP in the X-Forwarded-For list
        return xff.split(",")[0].strip()

    xrip = request.headers.get("x-real-ip")
    if xrip:
        return xrip.strip()

    # fallback: immediate peer IP
    return request.client.host if request.client else "unknown"

#----------Logger setup ----------
import logging
from pythonjsonlogger import jsonlogger

webhook_log_handler = logging.FileHandler("webhook.log")
webhook_formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
webhook_log_handler.setFormatter(webhook_formatter)

webhook_logger = logging.getLogger("webhook_logger")
webhook_logger.addHandler(webhook_log_handler)
webhook_logger.setLevel(logging.INFO)

# --------- Password generator setup ---------
letters = list("abcdefghjklmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ")
numbers = list("23456789")
symbols = list("!#$%()*+")
cases = [0, 0, 1, 1, 2]  # 0 = letter, 1 = number, 2 = symbol

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

# --------- Registration ---------
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

        result = usersCleaningSite.insert_one({
            "firstName": firstName,
            "lastName": lastName,
            "userName": userName,
            "email": email,
            "password": hashed_pw,
            "cellNum": cellNum,
            "created_at": datetime.now(UTC)
        })

        if usersCleaningSite.find_one({"_id": result.inserted_id}):
            return JSONResponse(content={"message": "User created successfully", "id": str(result.inserted_id)}, status_code=201)

        return JSONResponse(content={"error": "User insertion failed"}, status_code=500)

    except Exception as e:
        return JSONResponse(content={"error": f"Server error: {str(e)}"}, status_code=500)

# --------- Basic routes ---------
@app.get("/")
def root():
    return {"message": "Welcome to the KingBurger API"}

@app.get("/health")
def health_check():
    return {"status": "alive"}

# --------- JWT Login ---------
@app.post("/login/")
async def login(userName: str = Form(...), password: str = Form(...)):
    user = usersCleaningSite.find_one({"userName": userName})
    if not user or not argon2.verify(password, user["password"]):
        return JSONResponse(content={"error": "Invalid credentials"}, status_code=401)

    payload = {
        "user_id": str(user["_id"]),
        "exp": datetime.now(UTC) + timedelta(hours=1)  # token expires in 1 hour
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return JSONResponse(content={"message": "Login successful", "token": token, "user": {"firstName": user["firstName"]}})


@app.post("/logout/")
async def logout():
    return {"message": "Logout successful (client should discard the token)"}


# --------- Get Current User ---------
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
        user = usersCleaningSite.find_one({"_id": ObjectId(user_id)})
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

# ----------User endpoints ----------
@app.get("/users/{id}")
async def get_user(id: str, user=Depends(get_current_user)):
    try:
        user_data = get_user_by_id(id)
        if user_data:
            user_data["_id"] = str(user_data["_id"])
            del user_data["password"]
            return user_data
        return {"error": "User not found"}
    except Exception as e:
        return {"error": str(e)}

# --------- Product endpoints ---------
@app.post("/products/create/")
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: Union[str, None] = Form(None),
    category: int = Form(0),
    image_url: Union[str, None] = Form(None),
    user=Depends(get_current_user)
):
    try:
        result = products.insert_one({
            "name": name,
            "price": price,
            "description": description,
            "category": category,
            "image_url": image_url,
            "created_at": datetime.now(UTC)
        })
        return {"message": "Product created successfully", "id": str(result.inserted_id)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/products/")
async def get_all_products():
    try:
        all_products = []
        for product in products.find():
            product["_id"] = str(product["_id"])
            all_products.append(product)
        return all_products
    except Exception as e:
        return {"error": str(e)}

@app.get("/products/{id}")
async def get_product(id: str, user=Depends(get_current_user)):
    try:
        product = products.find_one({"_id": ObjectId(id)})
        if product:
            product["_id"] = str(product["_id"])
            return product
        return {"error": "Product not found"}
    except InvalidId:
        return {"error": "Invalid product ID"}
    except Exception as e:
        return {"error": str(e)}

@app.put("/products/update/{id}")
async def update_product(
    id: str,
    name: Union[str, None] = Form(None),
    price: Union[float, None] = Form(None),
    description: Union[str, None] = Form(None),
    category: Union[int, None] = Form(None),
    image_url: Union[str, None] = Form(None),
    user=Depends(get_current_user)
):
    try:
        update_data = {k: v for k, v in {
            "name": name,
            "price": price,
            "description": description,
            "category": category,
            "image_url": image_url
        }.items() if v is not None}

        result = products.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        if result.matched_count:
            return {"message": "Product updated successfully"}
        return {"error": "Product not found"}
    except InvalidId:
        return {"error": "Invalid product ID"}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/products/delete/{id}", include_in_schema=False)
async def delete_product(id: str, user=Depends(get_current_user)):
    try:
        result = products.delete_one({"_id": ObjectId(id)})
        if result.deleted_count:
            return {"message": "Product deleted successfully"}
        return {"error": "Product not found"}
    except InvalidId:
        return {"error": "Invalid product ID"}
    except Exception as e:
        return {"error": str(e)}

# --------- Payment endpoint ---------
class PaymentRequest(BaseModel):
    payment_type: str
    amount: float
    reference: str

@app.post("/api/create-payment", include_in_schema=False)
async def create_payment(payment: PaymentRequest):
    callpay_creds = generate_callpay_token()
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

    payload = {
        "amount": payment.amount,
        "merchant_reference": f"PAY{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{suffix}",
        "payment_type": payment.payment_type, 
        "notify_url": "https://kingburger.site/webhook",
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
            try:
                data = response.json()
            except Exception:
                data = {"raw_response": response.text or "No content returned"}
            return data
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"API error: {e.response.text}")

# --------- Webhook endpoint ---------

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
        payload = body_bytes.decode(errors="ignore")  # decode bytes to string
    except Exception:
        payload = str(body_bytes)

    webhook_logger.info({
        "event": "webhook_received",
        "client_ip": client_ip,
        "payload": payload
    })
    
    return JSONResponse({"status": "ok", "client_ip": client_ip})

# --------- Run server ---------
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("products.DB:app", host="0.0.0.0", port=port, reload=True)
