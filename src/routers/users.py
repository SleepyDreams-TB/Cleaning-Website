"""
USERS ROUTER - Handles user profile operations
This file manages: viewing user profiles, updating user info
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Form
from bson import ObjectId
from bson.errors import InvalidId
from typing import Optional
from passlib.hash import argon2 as ph

from helpers_routers.helpers import get_current_user
from databaseConnections.mongoClient import get_collection

router = APIRouter(prefix="/users", tags=["users"])

users_collection = get_collection("store_users")


# ==================== GET DASHBOARD INFO ====================
@router.get("/dashboard/info")
async def get_dashboard_info(current_user=Depends(get_current_user)):
    """
    Get dashboard information for the logged-in user.
    Requires: valid httpOnly cookie
    """
    return {
        "success": True,
        "profileImageUrl": current_user.get("profileImageUrl"),
        "loggedIn_User": current_user["firstName"],
        "user_id": str(current_user["_id"]),
        "userName": current_user.get("userName"),
        "email": current_user.get("email"),
        "billing_address": (
            current_user.get("billing_info", {})
                        .get("billing_address", {})
        )
    }


# ==================== ADD/UPDATE BILLING ADDRESS ====================
@router.post("/update/billing/address")
async def add_or_update_billing_address(
    request: Request,
    current_user=Depends(get_current_user)
):
    billing_address = await request.json()
    address_name = billing_address.get("address_name")

    if not address_name:
        raise HTTPException(status_code=400, detail="Address name is required")

    # Remove address_name from the object before storing
    billing_address.pop("address_name")

    try:
        update_result = users_collection.update_one(
            {"_id": ObjectId(current_user["_id"])},
            {"$set": {f"billing_info.billing_address.{address_name}": billing_address}}
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


# ==================== GET USER BY ID ====================
@router.get("/{user_id}")
async def get_user_profile(user_id: str, current_user=Depends(get_current_user)):
    """
    Get a user's profile by their ID.
    Users can only access their own profile.
    """
    # ── Ownership check — users can only fetch their own profile ──
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this profile")

    try:
        target_user = users_collection.find_one({"_id": ObjectId(user_id)})

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Remove sensitive fields before returning
        target_user.pop("password", None)
        target_user.pop("2fa_secret", None)
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


# ==================== UPDATE USER PROFILE ====================
@router.put("/{user_id}")
async def update_user_profile(
    user_id: str,
    current_user=Depends(get_current_user),
    userName: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    firstName: Optional[str] = Form(None),
    lastName: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    cellNum: Optional[str] = Form(None),
):
    """
    Update a user's profile.
    Users can only update their own profile.
    """
    # ── Ownership check ──
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")

    try:
        safe_data = {
            k: v for k, v in {
                "firstName": firstName,
                "lastName": lastName,
                "email": email,
                "cellNum": cellNum,
                "userName": userName,
                "password": password
            }.items()
            if v is not None and v.strip() != ""
        }

        if not safe_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        if "password" in safe_data:
            safe_data["password"] = ph.hash(safe_data["password"])

        if "userName" in safe_data:
            existing = users_collection.find_one({"userName": safe_data["userName"]})
            if existing and str(existing["_id"]) != user_id:
                raise HTTPException(status_code=400, detail="Username already taken")

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


# ==================== DELETE USER PROFILE ====================
@router.delete("/{user_id}")
async def delete_user_profile(user_id: str, current_user=Depends(get_current_user)):
    """
    Delete a user's profile.
    Users can only delete their own profile.
    """
    # ── Ownership check ──
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this profile")

    try:
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