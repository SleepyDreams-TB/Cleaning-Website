"""
AUTHENTICATION ROUTER - Handles user registration, login, and logout
This file manages: user signup, login with JWT tokens, and logout
"""

from fastapi import APIRouter, Form, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
from pydantic import EmailStr
from passlib.hash import argon2
from typing import Union
import jwt
import os
from datetime import datetime, timedelta, timezone

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "your-mongo-connection-string")
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client["cleaning_website"]
users_collection = db["usersCleaningSite"]

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
UTC = timezone.utc

# ==================== HELPER FUNCTIONS ====================
def check_user_exists(userName: str, email: str):
    """Check if username or email already exists in database"""
    try:
        user = users_collection.find_one({
            "$or": [{"userName": userName}, {"email": email}]
        })
        return user is not None
    except Exception as e:
        print(f"❌ check_user_exists error: {e}")
        return False

def get_current_user(authorization: str = Header(...)):
    """
    Get the currently logged-in user from JWT token
    This is used as a dependency in protected routes
    """
    # Check if header starts with "Bearer "
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header format")
    
    # Extract the token
    token = authorization.split(" ")[1]
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
        
        # Find user in database
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired - please login again")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== REGISTER NEW USER ====================
@router.post("/register")
async def register_user(
    firstName: str = Form(...),
    lastName: str = Form(...),
    userName: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    cellNum: Union[str, None] = Form(None)
):
    """
    Register a new user account
    
    Required fields:
    - firstName: User's first name
    - lastName: User's last name
    - userName: Unique username
    - email: Unique email address
    - password: User's password (will be hashed)
    - cellNum: Optional phone number
    """
    try:
        # Check if username or email already exists
        if check_user_exists(userName, email):
            return JSONResponse(
                content={"error": "Username or email already exists"},
                status_code=400
            )
        
        # Hash the password for security
        hashed_password = argon2.hash(password)
        
        # Create new user document
        new_user = {
            "firstName": firstName,
            "lastName": lastName,
            "userName": userName,
            "email": email,
            "password": hashed_password,
            "cellNum": cellNum,
            "created_at": datetime.now(UTC)
        }
        
        # Insert into database
        result = users_collection.insert_one(new_user)
        
        if result.inserted_id:
            return JSONResponse(
                content={
                    "success": True,
                    "message": "User created successfully!",
                    "user_id": str(result.inserted_id)
                },
                status_code=201
            )
        
        return JSONResponse(
            content={"error": "User registration failed"},
            status_code=500
        )
    
    except Exception as error:
        print(f"❌ Registration error: {error}")
        return JSONResponse(
            content={"error": f"Server error: {str(error)}"},
            status_code=500
        )

# ==================== LOGIN USER ====================
@router.post("/login")
async def login_user(
    userName: str = Form(...),
    password: str = Form(...)
):
    """
    Login with username and password
    Returns a JWT token for authentication
    
    Example response:
    {
        "success": true,
        "message": "Login successful",
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {"firstName": "John", "user_id": "123"}
    }
    """
    try:
        # Find user by username
        user = users_collection.find_one({"userName": userName})
        
        if not user:
            return JSONResponse(
                content={"error": "Invalid username or password"},
                status_code=401
            )
        
        # Verify password
        try:
            password_correct = argon2.verify(password, user.get("password", ""))
            if not password_correct:
                return JSONResponse(
                    content={"error": "Invalid username or password"},
                    status_code=401
                )
        except Exception as verify_error:
            print(f"❌ Password verify error for '{userName}': {verify_error}")
            return JSONResponse(
                content={"error": "Invalid username or password"},
                status_code=401
            )
        
        # Create JWT token (expires in 1 hour)
        token_payload = {
            "user_id": str(user["_id"]),
            "exp": datetime.now(UTC) + timedelta(hours=1)
        }
        token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        return JSONResponse({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "firstName": user["firstName"],
                "user_id": str(user["_id"]),
                "userName": user["userName"]
            }
        })
    
    except Exception as error:
        print(f"❌ Login error: {error}")
        return JSONResponse(
            content={"error": f"Server error: {str(error)}"},
            status_code=500
        )

# ==================== LOGOUT USER ====================
@router.post("/logout")
async def logout_user():
    """
    Logout user
    Note: JWT tokens are stateless, so the client should simply discard the token
    """
    return {
        "success": True,
        "message": "Logout successful (client should discard the token)"
    }

# ==================== GET CURRENT USER INFO ====================
@router.get("/me")
async def get_my_info(user = Depends(get_current_user)):
    """
    Get information about the currently logged-in user
    Requires: Valid JWT token in Authorization header
    
    Example: GET /auth/me
    Header: Authorization: Bearer your-jwt-token
    """
    return {
        "success": True,
        "user": {
            "user_id": str(user["_id"]),
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "userName": user["userName"],
            "email": user["email"],
            "cellNum": user.get("cellNum"),
            "created_at": user.get("created_at")
        }
    }
