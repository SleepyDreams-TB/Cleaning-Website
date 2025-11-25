"""
USERS ROUTER - Handles user profile operations
This file manages: viewing user profiles, updating user info
"""

from fastapi import APIRouter, HTTPException, Depends , Request
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import os
import argon2

# Import the auth dependency
from auth import get_current_user
from helpers import billing_info_helper

router = APIRouter(prefix="/users", tags=["users"])

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "your-mongo-connection-string")
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client["cleaning_website"]
users_collection = db["usersCleaningSite"]

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")



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
        "loggedIn_User": {current_user['firstName']},
        "user_id": str(current_user["_id"]),
        "userName": current_user.get("userName"),
        "email": current_user.get("email"),
        "billing_address": billing_info_helper(current_user)
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
    
# ==================== ADD/UPDATE BILLING ADDRESS ====================
@router.post("/update/billing/address")
async def add_or_update_billing_address(request: Request, current_user = Depends(get_current_user)):
    billing_address = await request.json()
    address_name = billing_address.get("address_name")

    if not address_name:
        raise HTTPException(status_code=400, detail="Address name is required")

    # Remove address_name from the object to store the rest
    billing_address.pop("address_name")

    try:
        update_result = users_collection.update_one(
            {"_id": ObjectId(current_user["_id"])},
            {"$set": {f"billing_info.billing_address.{address_name}": billing_address}},
            upsert=True
        )

        if update_result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "message": "Billing information updated successfully"
        }

    except Exception as error:
        print(f"❌ Error updating billing info for user {current_user['_id']}: {error}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(error)}")

# ==================== DELETE USER PROFILE ====================

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
