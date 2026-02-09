"""
PRODUCTS ROUTER - Handles all cleaning product operations
This file manages: viewing, creating, updating, and deleting cleaning products
"""

from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import os

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create a router (like a mini-app for products)
router = APIRouter(prefix="/products", tags=["products"])

# Connect to MongoDB database
MONGO_URI = os.getenv("MONGO_URI","mongodb+srv://SleepyDreams:saRqSb7xoc1cI1DO@kingburgercluster.ktvavv3.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client["kingburgerstore_db"]
products_collection = db["products"]  # This is our products table

# ==================== DATA MODELS ====================
# These define what data we expect when creating/updating products

class ProductCreate(BaseModel):
    """What we need when creating a new product"""
    name: str  # Example: "Home Cleaning Service"
    price: float  # Example: 150.00
    description: str  # Example: "Full home cleaning including bedrooms..."
    category: int  # 1=Services, 2=Supplies, 3=Packages
    image_url: Optional[str] = None  # Example: "https://..."

class ProductUpdate(BaseModel):
    """What we can update (all fields are optional)"""
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[int] = None
    image_url: Optional[str] = None

# ==================== HELPER FUNCTION ====================
def clean_product_data(product):
    """
    Convert MongoDB's _id (ObjectId) to a regular string 'id'
    This makes it JSON-friendly for sending to frontend
    """
    if product:
        product["id"] = str(product["_id"])  # Convert ObjectId to string
        del product["_id"]  # Remove the old _id field
    return product

# ==================== GET ALL PRODUCTS ====================
@router.get("/")
async def get_all_products(category: Optional[int] = None):
    """
    Get all cleaning products from database
    
    Examples:
    - GET /products/ → returns all products
    - GET /products/?category=1 → returns only category 1 (services)
    """
    try:
        # Build search query
        search_query = {}
        if category:
            search_query["category"] = category
        
        # Get products from database (newest first)
        products = list(products_collection.find(search_query).sort("created_at", -1))
        
        # Clean up the data for frontend
        cleaned_products = [clean_product_data(p) for p in products]
        
        return {
            "success": True,
            "count": len(cleaned_products),
            "products": cleaned_products
        }
    
    except Exception as error:
        print(f"❌ Error getting products: {error}")
        raise HTTPException(status_code=500, detail="Could not fetch products")

# ==================== GET ONE PRODUCT ====================
@router.get("/{product_id}")
async def get_single_product(product_id: str):
    """
    Get one specific product by its ID
    
    Example: GET /products/68ded7ef3ca60b183a391f4a
    """
    try:
        # Find product in database
        product = products_collection.find_one({"_id": ObjectId(product_id)})
        
        # Check if we found it
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "product": clean_product_data(product)
        }
    
    except Exception as error:
        print(f"❌ Error getting product {product_id}: {error}")
        raise HTTPException(status_code=500, detail="Could not fetch product")

# ==================== CREATE NEW PRODUCT ====================
@router.post("/")
async def create_new_product(product_data: ProductCreate):
    """
    Create a brand new cleaning product
    
    Example request body:
    {
        "name": "Deep Clean Package",
        "price": 299.99,
        "description": "Complete deep cleaning service",
        "category": 3,
        "image_url": "https://example.com/image.jpg"
    }
    """
    try:
        # Prepare the product data
        new_product = {
            "name": product_data.name,
            "price": product_data.price,
            "description": product_data.description,
            "category": product_data.category,
            "image_url": product_data.image_url,
            "created_at": datetime.now(timezone.utc)  # Add timestamp
        }
        
        # Insert into database
        result = products_collection.insert_one(new_product)
        
        # Get the newly created product
        created_product = products_collection.find_one({"_id": result.inserted_id})
        
        return {
            "success": True,
            "message": "Product created successfully!",
            "product": clean_product_data(created_product)
        }
    
    except Exception as error:
        print(f"❌ Error creating product: {error}")
        raise HTTPException(status_code=500, detail="Could not create product")

# ==================== UPDATE PRODUCT ====================
@router.put("/{product_id}")
async def update_existing_product(product_id: str, updates: ProductUpdate):
    """
    Update an existing product
    You only need to send the fields you want to change
    
    Example: PUT /products/68ded7ef3ca60b183a391f4a
    Body: {"price": 199.99, "name": "Updated Name"}
    """
    try:
        # Only include fields that were actually provided
        update_fields = {}
        if updates.name is not None:
            update_fields["name"] = updates.name
        if updates.price is not None:
            update_fields["price"] = updates.price
        if updates.description is not None:
            update_fields["description"] = updates.description
        if updates.category is not None:
            update_fields["category"] = updates.category
        if updates.image_url is not None:
            update_fields["image_url"] = updates.image_url
        
        # Check if there's anything to update
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update in database
        result = products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_fields}
        )
        
        # Check if product was found
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get the updated product
        updated_product = products_collection.find_one({"_id": ObjectId(product_id)})
        
        return {
            "success": True,
            "message": "Product updated successfully!",
            "product": clean_product_data(updated_product)
        }
    
    except Exception as error:
        print(f"❌ Error updating product {product_id}: {error}")
        raise HTTPException(status_code=500, detail="Could not update product")

# ==================== DELETE PRODUCT ====================
@router.delete("/{product_id}")
async def delete_product(product_id: str):
    """
    Delete a product permanently
    
    Example: DELETE /products/68ded7ef3ca60b183a391f4a
    """
    try:
        # Delete from database
        result = products_collection.delete_one({"_id": ObjectId(product_id)})
        
        # Check if product was found and deleted
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "message": "Product deleted successfully!",
            "deleted_id": product_id
        }
    
    except Exception as error:
        print(f"❌ Error deleting product {product_id}: {error}")
        raise HTTPException(status_code=500, detail="Could not delete product")

# ==================== GET BY CATEGORY ====================
@router.get("/category/{category_number}")
async def get_products_by_category(category_number: int):
    """
    Get all products in a specific category
    
    Categories:
    1 = Cleaning Services (Home Cleaning, Office Cleaning, etc.)
    2 = Cleaning Supplies (Detergents, Mops, Brushes, etc.)
    3 = Packages (Monthly subscriptions, Bundle deals, etc.)
    
    Example: GET /products/category/1 → gets all cleaning services
    """
    try:
        # Find all products with this category
        products = list(
            products_collection.find({"category": category_number})
            .sort("created_at", -1)
        )
        
        # Clean up the data
        cleaned_products = [clean_product_data(p) for p in products]
        
        # Category names for reference
        category_names = {
            1: "Cleaning Services",
            2: "Cleaning Supplies",
            3: "Packages"
        }
        
        return {
            "success": True,
            "category": category_number,
            "category_name": category_names.get(category_number, "Unknown"),
            "count": len(cleaned_products),
            "products": cleaned_products
        }
    
    except Exception as error:
        print(f"❌ Error getting category {category_number}: {error}")
        raise HTTPException(status_code=500, detail="Could not fetch category products")