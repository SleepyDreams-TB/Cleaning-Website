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
import jwt
from datetime import datetime, timedelta, timezone
import os

from .orders import router as orders_router  # SQL-based orders router
from .products import router as products_router  # Products router
from .password_generator import router as password_generator_router
from  .payment import router as payments_router

# ------------------- Environment / Constants -------------------
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
CALLPAY_API_URL = os.getenv("CALLPAY_API_URL")
IP_WHITELIST = os.getenv("IP_WHITELIST", "54.72.191.28,54.194.139.201").split(",")

UTC = timezone.utc
#
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
    return {
        "loggedIn_User": f"{user['firstName']}!",
        "user_id": str(user["_id"]),
        "userName": user.get("userName")
    }


@app.get("/users/{user_id}")
async def get_user(user_id: str, user=Depends(get_current_user)):
    """Get user by ID - requires authentication"""
    try:
        target_user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        target_user.pop("password", None)
        target_user["_id"] = str(target_user["_id"])
        
        return target_user
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")




# ------------------- Include Orders Router (SQLAlchemy) -------------------
app.include_router(orders_router)
app.include_router(products_router)
app.include_router(password_generator_router)
app.include_router(payments_router)
# ------------------- Run Server -------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
