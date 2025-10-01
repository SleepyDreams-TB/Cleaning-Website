from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from fastapi import FastAPI, Form, HTTPException
from typing import Union
from bson import ObjectId
import ssl
import sys
from contextlib import asynccontextmanager
from pydantic import BaseModel
from callpayV2_Token import generate_callpay_token
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Python version:", sys.version)
    print("OpenSSL version:", ssl.OPENSSL_VERSION)
    yield

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient(
    "mongodb+srv://SleepyDreams:saRqSb7xoc1cI1DO@kingburgercluster.ktvavv3.mongodb.net/?retryWrites=true&w=majority",
    tls=True,
    tlsAllowInvalidCertificates=False
)
db = client["cleaning_website"]
products = db["products"]

# Product routes
@app.get("/")
def root():
    return {"message": "Welcome to the Products API"}

@app.get("/health")
def health_check():
    return {"status": "alive"}

@app.post("/products/create/")
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    description: Union[str, None] = Form(None),
    category: int = Form(0),
    image_url: Union[str, None] = Form(None)
):
    try:
        result = products.insert_one({
            "name": name,
            "price": price,
            "description": description,
            "category": category,
            "image_url": image_url
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
async def get_product(id: str):
    try:
        product = products.find_one({"_id": ObjectId(id)})
        if product:
            product["_id"] = str(product["_id"])
            return product
        return {"message": "Product not found"}
    except Exception as e:
        return {"error": str(e)}

@app.put("/products/update/{id}")
async def update_product(
    id: str,
    name: Union[str, None] = Form(None),
    price: Union[float, None] = Form(None),
    description: Union[str, None] = Form(None),
    category: Union[int, None] = Form(None),
    image_url: Union[str, None] = Form(None)
):
    try:
        # Explicitly build update_data
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if price is not None:
            update_data["price"] = price
        if description is not None:
            update_data["description"] = description
        if category is not None:
            update_data["category"] = category
        if image_url is not None:
            update_data["image_url"] = image_url

        result = products.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        if result.matched_count:
            return {"message": "Product updated successfully"}
        return {"message": "Product not found"}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/products/delete/{id}")
async def delete_product(id: str):
    try:
        result = products.delete_one({"_id": ObjectId(id)})
        if result.deleted_count:
            return {"message": "Product deleted successfully"}
        return {"message": "Product not found"}
    except Exception as e:
        return {"error": str(e)}

# Payment
class PaymentRequest(BaseModel):
    payment_type: str
    amount: float
    reference: str

CALLPAY_API_URL = "https://services.callpay.com/api/v2/payment-key"

@app.post("/api/create-payment")
async def create_payment(payment: PaymentRequest):
    # Generate fresh token and credentials for each request
    callpay_creds = generate_callpay_token()

    payload = {
        "amount": payment.amount,
        "merchant_reference": payment.reference,
        "payment_type": payment.payment_type
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

            # Debug logs
            print("Status code:", response.status_code)
            print("Response headers:", response.headers)
            print("Raw response:", repr(response.text))

            try:
                data = response.json()
            except Exception:
                data = {"raw_response": response.text or "No content returned"}

            return data

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"API error: {e.response.text}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("products.productsDB:app", host="0.0.0.0", port=port)
