"""
PRODUCTS ROUTER - Handles all cleaning product operations
This file manages: viewing, creating, updating, and deleting cleaning products
"""

from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from typing import Optional, List
from datetime import datetime, timezone
import os
from models import ProductCreate, ProductUpdate

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create a router (like a mini-app for products)
router = APIRouter(prefix="/products", tags=["products"])

# Connect to MongoDB database
MONGO_URI = os.getenv("MONGO_URI","mongodb+srv://SleepyDreams:saRqSb7xoc1cI1DO@kingburgercluster.ktvavv3.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
db = client["kingburgerstore_db"]
products_collection = db["products"]  # This is our products table

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
    Create a brand new product with full details
    
    Example request body:
    {
        "name": "Intel Core i5-12400F",
        "description": "6-core 12-thread desktop processor...",
        "price": 3499,
        "category": 1,
        "slug": "intel-core-i5-12400f",
        "short_description": "12th Gen 6-core CPU",
        "brand": "Intel",
        "sku": "CPU-INT-12400F",
        "image_url": "https://example.com/image.jpg",
        ...
    }
    """
    try:
        # Prepare the product data - include ALL fields from ProductCreate
        new_product = {
            "name": product_data.name,
            "description": product_data.description,
            "price": product_data.price,
            "category": product_data.category,
            "created_at": datetime.now(timezone.utc),
            # Optional fields
            "slug": product_data.slug,
            "short_description": product_data.short_description,
            "compare_at_price": product_data.compare_at_price,
            "currency": product_data.currency,
            "brand": product_data.brand,
            "sku": product_data.sku,
            "image_url": str(product_data.image_url) if product_data.image_url else None,
            "images": [str(img) for img in product_data.images] if product_data.images else None,
            "stock_quantity": product_data.stock_quantity,
            "availability_status": product_data.availability_status,
            "specifications": product_data.specifications,
            "weight_kg": product_data.weight_kg,
            "is_active": product_data.is_active,
            "tags": product_data.tags,
            "meta_title": product_data.meta_title,
            "meta_description": product_data.meta_description,
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


# ==================== Bulk Create NEW PRODUCT ====================
@router.post("/bulk")
async def create_bulk_products(products: List[ProductCreate]):
    """
    Create multiple products at once (bulk upload)
    
    Example request body:
    [
        {
            "name": "Product 1",
            "description": "...",
            "price": 150.00,
            "category": 1,
            "slug": "product-1",
            ...
        },
        {
            "name": "Product 2",
            "description": "...",
            "price": 9.99,
            "category": 2,
            ...
        }
    ]
    """
    try:
        # Prepare the product data for bulk insert
        new_products = []
        for product in products:
            new_products.append({
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "category": product.category,
                "created_at": datetime.now(timezone.utc),
                # Optional fields
                "slug": product.slug,
                "short_description": product.short_description,
                "compare_at_price": product.compare_at_price,
                "currency": product.currency,
                "brand": product.brand,
                "sku": product.sku,
                "image_url": str(product.image_url) if product.image_url else None,
                "images": [str(img) for img in product.images] if product.images else None,
                "stock_quantity": product.stock_quantity,
                "availability_status": product.availability_status,
                "specifications": product.specifications,
                "weight_kg": product.weight_kg,
                "is_active": product.is_active,
                "tags": product.tags,
                "meta_title": product.meta_title,
                "meta_description": product.meta_description,
            })
        
        # Insert into database
        result = products_collection.insert_many(new_products)
        
        # Get the newly created products
        created_products = list(products_collection.find({"_id": {"$in": result.inserted_ids}}))
        
        return {
            "success": True,
            "message": f"{len(created_products)} products created successfully!",
            "products": [clean_product_data(p) for p in created_products]
        }
    
    except Exception as error:
        print(f"❌ Error creating bulk products: {error}")
        raise HTTPException(status_code=500, detail="Could not create products")


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
        
        # Check each field and add to update if provided
        if updates.name is not None:
            update_fields["name"] = updates.name
        if updates.slug is not None:
            update_fields["slug"] = updates.slug
        if updates.short_description is not None:
            update_fields["short_description"] = updates.short_description
        if updates.description is not None:
            update_fields["description"] = updates.description
        if updates.price is not None:
            update_fields["price"] = updates.price
        if updates.compare_at_price is not None:
            update_fields["compare_at_price"] = updates.compare_at_price
        if updates.currency is not None:
            update_fields["currency"] = updates.currency
        if updates.brand is not None:
            update_fields["brand"] = updates.brand
        if updates.sku is not None:
            update_fields["sku"] = updates.sku
        if updates.category is not None:
            update_fields["category"] = updates.category
        if updates.image_url is not None:
            update_fields["image_url"] = updates.image_url
        if updates.images is not None:
            update_fields["images"] = updates.images
        if updates.stock_quantity is not None:
            update_fields["stock_quantity"] = updates.stock_quantity
        if updates.availability_status is not None:
            update_fields["availability_status"] = updates.availability_status
        if updates.specifications is not None:
            update_fields["specifications"] = updates.specifications
        if updates.weight_kg is not None:
            update_fields["weight_kg"] = updates.weight_kg
        if updates.is_active is not None:
            update_fields["is_active"] = updates.is_active
        if updates.tags is not None:
            update_fields["tags"] = updates.tags
        if updates.meta_title is not None:
            update_fields["meta_title"] = updates.meta_title
        if updates.meta_description is not None:
            update_fields["meta_description"] = updates.meta_description
        
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