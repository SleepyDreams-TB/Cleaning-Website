#AUTHENTICATION ROUTER - Handles user registration, login, and logout
#This file manages: user signup, login with JWT #tokens, and logout


from fastapi import APIRouter, Form, HTTPException, Depends, Response, Request
from fastapi.responses import JSONResponse 
from pymongo import MongoClient
from bson import ObjectId
from pydantic import EmailStr
from passlib.hash import argon2
from typing import Union, cast
import jwt
import os
from datetime import datetime, timedelta, timezone

#QR code library
import base64
import pyotp
import qrcode
import io
from qrcode.image.pil import PilImage

from limiter import limiter

from helpers_routers.helpers import get_current_user
from databaseConnections.mongoClient import get_collection

users_collection = get_collection("store_users")
# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# MongoDB connection


# JWT Settings
SECRET_KEY = cast(str, os.getenv("SECRET_KEY"))
ALGORITHM = cast(str, os.getenv("ALGORITHM", "HS256"))
ROLES = [role.strip() for role in os.getenv("ROLES", "").split(",") if role.strip()]
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

    

def generate_qr(user_id: str):
    """
    Placeholder for future 2FA authentication implementation
    """
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    user_2fa_secret = user.get("2fa_secret")
    user_2fa_registered = user.get("2fa_registered", False)

    if user_2fa_registered:
        return {
            "success": True,
            "registered": True,
            "message": "2FA already registered"
        }

    if not user_2fa_secret:
        user_2fa_secret = pyotp.random_base32()
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"2fa_secret": user_2fa_secret}}
        )

    issuer_name = "KingburgerStore"
    otpauth_uri = pyotp.totp.TOTP(user_2fa_secret).provisioning_uri(
        name=user["email"], issuer_name=issuer_name
    )

    # Generate QR and encode as Base64
    qr_img = qrcode.make(otpauth_uri,  image_factory=PilImage)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_bytes = buf.getvalue()
    qr_base64 = base64.b64encode(qr_bytes).decode("utf-8")

    return {
        "success": True,
        "registered": False,
        "message": "QR code generated successfully",
        "qr_image": qr_base64
    }
# ==================== REGISTER NEW USER ====================
@router.post("/register")
async def register_user(
    firstName: str = Form(...),
    lastName: str = Form(...),
    userName: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    cellNum: Union[str, None] = Form(None),
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
            "created_at": datetime.now(UTC),
            "2fa_registered": False,
            "2fa_secret": pyotp.random_base32(),
            "role": "customer" 
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

# ==================== LOGOUT USER ====================
@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return {"success": True, "message": "Logged out successfully"}

# ==================== GET CURRENT USER INFO ====================
@router.get("/me")
async def get_my_info(user = Depends(get_current_user)):
    """
    Get information about the currently logged-in user
    Requires: Valid JWT token in Authorization header
    
    Example: GET /auth/me
    Header: Authorization: Bearer your-jwt-token
    """
    billing_info_set = "billing_info" in user and user["billing_info"] is not None

    return {
        "success": True,
        "user": {
            "user_id": str(user["_id"]),
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "userName": user["userName"],
            "email": user["email"],
            "cellNum": user.get("cellNum"),
            "created_at": user.get("created_at"),
            "billing_info_set": billing_info_set
        }
    }

# ==================== LOGIN STEP ====================

@router.post("/login-step")
@limiter.limit("5/minute")

def login_step(request: Request, userName: str = Form(...), password: str = Form(...)):
    try:
        print(f"🔹 Login attempt for username: {userName}")
        user = users_collection.find_one({"userName": userName})
        if not user:
            print("❌ User not found")
            return JSONResponse({"error": "Invalid username or password"}, status_code=401)
        # Verify password
        try:
            password_correct = argon2.verify(password, user.get("password", ""))
            if not password_correct:
                print("❌ Password incorrect")
                return JSONResponse({"error": "Invalid username or password"}, status_code=401)
        except Exception as verify_error:
            print(f"❌ Password verify error: {verify_error}")
            return JSONResponse({"error": "Invalid username or password"}, status_code=401)

        # Generate QR for 2FA
        try:
            result = generate_qr(str(user["_id"]))
            if result["success"] and not result["registered"]:
                return JSONResponse({
                    "success": True,
                    "user_id": str(user["_id"]),
                    "registered": False,
                    "qr_code": f"data:image/png;base64,{result['qr_image']}",
                    "message": "2FA not registered, please scan QR code"
                }, status_code=200)
            else:
                return JSONResponse({
                    "success": True,
                    "user_id": str(user["_id"]),
                    "registered": True,
                    "message": "2FA already registered, proceed to login"
                }, status_code=200)
        except Exception as e:
            return JSONResponse({"success": False, "message": f"Error generating QR: {str(e)}"}, status_code=500)

    except Exception as error:
        return JSONResponse({"error": f"Server error: {str(error)}"}, status_code=500)



# ==================== QR STEP ====================

@router.post("/qr-step")
def qr_step(request: Request, user_id: str = Form(...), digit_code: str = Form(...)):
    
    """
    QR code step for 2FA authentication
    """
    try:

        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return JSONResponse(
                content={"error": "User not found"},
                status_code=404
                )

        secret = user.get("2fa_secret")
        if not secret:
            return JSONResponse(
                content={"error": "2FA not set up for this user"},
                status_code=400
            )

        is_valid = pyotp.TOTP(secret).verify(digit_code)
        
        if not is_valid:
            return JSONResponse(
                content={"error": "Invalid 2FA code"},
                status_code=401
            )
        if not user.get("2fa_registered", False):
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"2fa_registered": True}}
            )

        try:
            # Create JWT token (expires in 1 hour)
            token_payload = {
                "user_id": str(user_id),
                "exp": datetime.now(UTC) + timedelta(hours=1)
            }
            token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

            json_response = JSONResponse({
                "success": True,
                "message": "Login successful",
                "user": {
                    "firstName": user["firstName"],
                    "user_id": str(user["_id"]),
                    "userName": user["userName"]
                }
            })

            json_response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=3600
            )

            return json_response
        
        except Exception as error:
            return JSONResponse(
                content={"error": f"Server error: {str(error)}"},
                status_code=500
            )

    except Exception as error:
        return JSONResponse(
            content={"error": f"Server error: {str(error)}"},
            status_code=500
        )