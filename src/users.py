"""
USERS ROUTER - Handles user profile operations
This file manages: viewing user profiles, updating user info
"""

from fastapi import APIRouter, HTTPException, Depends
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import os
import argon2

# Import the auth dependency
# NOTE: You'll need to import get_current_user from auth.py
# from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "your-mongo-connection-string")
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client["cleaning_website"]
users_collection = db["usersCleaningSite"]

# ==================== TEMPORARY AUTH DEPENDENCY ====================
# This is a placeholder - replace with: from .auth import get_current_user
from fastapi import Header
import jwt
from datetime import timezone

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def get_current_user(authorization: str = Header(...)):
    """Get currently logged-in user (imported from auth.py in production)"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = users_collection.find_one({"_id": ObjectId(payload["user_id"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== GET USER BY ID ====================
@router.get("/{user_id}")
async def get_user_profile(user_id: str, current_user = Depends(get_current_user)):
    """
    Get a user's profile by their ID
    Requires authentication (must be logged in)
    
    Example: GET /users/68f7a75bbe7aff100435ab4e
    Header: Authorization: Bearer your-jwt-token
    """
    try:
        # Find the user in database
        target_user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove sensitive information (password)
        target_user.pop("password", None)
        
        # Convert ObjectId to string for JSON
        target_user["_id"] = str(target_user["_id"])
        
        return {
            "success": True,
            "user": target_user
        }
    
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    except HTTPException:
        raise
    
    except Exception as error:
        print(f"❌ Error fetching user {user_id}: {error}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(error)}")

# ==================== GET DASHBOARD INFO ====================
@router.get("/dashboard/info")
async def get_dashboard_info(current_user = Depends(get_current_user)):
    """
    Get dashboard information for the logged-in user
    
    Example: GET /users/dashboard/info
    Header: Authorization: Bearer your-jwt-token
    """
    return {
        "success": True,
        "loggedIn_User": f"Welcome back, {current_user['firstName']}!",
        "user_id": str(current_user["_id"]),
        "userName": current_user.get("userName"),
        "email": current_user.get("email")
    }

# Note: Additional user-related routes (e.g., update profile, delete account) TO-DO here.

ALLOWED_UPDATE_FIELDS = {"userName", "password","firstName", "lastName", "email", "cellNum"}

# ==================== Update User Profile ====================
@router.put("/{user_id}")
async def update_user_profile(user_id: str, user_data: dict, current_user = Depends(get_current_user)):
    """
    Update a user's profile by their ID
    Requires authentication (must be logged in)
    
    Example: PUT /users/68f7a75bbe7aff100435ab4e
    Header: Authorization: Bearer your-jwt-token
    Body: {
        "firstName": "NewFirstName",
        "lastName": "NewLastName",
        ...
    }
    """

    try:
        # Ensure the user is updating their own profile
        if str(current_user["_id"]) != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this profile")
        
        safe_data = {k: v for k, v in user_data.items() if k in ALLOWED_UPDATE_FIELDS}
        user_data = safe_data

        if not safe_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        if "password" in safe_data:
            safe_data["password"] = argon2.hash(safe_data["password"])

        if "userName" in safe_data:
            existing = users_collection.find_one({"userName": safe_data["userName"]})
            if existing and str(existing["_id"]) != user_id:
                raise HTTPException(status_code=400, detail="Username already taken")

        # Update the user in database
        update_result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": safe_data}
        )
        
        if update_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "message": "User profile updated successfully"
        }
    
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    except HTTPException:
        raise
    
    except Exception as error:
        print(f"❌ Error updating user {user_id}: {error}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(error)}")
    

@router.delete("/{user_id}")
async def delete_user_profile(user_id: str, current_user = Depends(get_current_user)):
    """
    Delete a user's profile by their ID
    Requires authentication (must be logged in)
    
    Example: DELETE /users/68f7a75bbe7aff100435ab4e
    Header: Authorization: Bearer your-jwt-token
    """
    try:
        # Ensure the user is deleting their own profile
        if str(current_user["_id"]) != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this profile")
        
        # Delete the user from database
        delete_result = users_collection.delete_one({"_id": ObjectId(user_id)})
        
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "message": "User profile deleted successfully"
        }
    
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    except HTTPException:
        raise
    
    except Exception as error:
        print(f"❌ Error deleting user {user_id}: {error}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(error)}")
