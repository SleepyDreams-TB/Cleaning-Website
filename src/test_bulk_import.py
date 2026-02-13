"""
DIAGNOSTIC TEST SCRIPT
Run this locally to test your bulk import data and MongoDB connection
"""

import json
from datetime import datetime, timezone
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict

# ==================== MOCK DATA ====================
# This is the exact data you're trying to import
SAMPLE_BULK_DATA = [
    {
        "name": "Intel Core i5-12400F",
        "slug": "intel-core-i5-12400f",
        "short_description": "12th Gen 6-core CPU",
        "description": "6-core 12-thread desktop processor with 12MB cache, LGA1700 socket.",
        "price": 3499,
        "compare_at_price": 3999,
        "currency": "ZAR",
        "brand": "Intel",
        "sku": "CPU-INT-12400F",
        "category": 1,
        "image_url": "https://m.media-amazon.com/images/I/61mFb2WuKUL.jpg",
        "images": [
            "https://m.media-amazon.com/images/I/61mFb2WuKUL.jpg",
            "https://m.media-amazon.com/images/I/61fV+QXjFAL.jpg"
        ],
        "stock_quantity": 25,
        "availability_status": "in_stock",
        "specifications": {
            "socket": "LGA1700",
            "cores": "6",
            "threads": "12",
            "base_clock": "2.5GHz",
            "boost_clock": "4.4GHz"
        },
        "weight_kg": 0.45,
        "is_active": True,
        "tags": ["cpu", "intel", "desktop", "gaming"],
        "meta_title": "Intel Core i5-12400F CPU | Buy Online",
        "meta_description": "Shop Intel 12th Gen 6-core CPU in South Africa"
    }
]

# ==================== PYDANTIC MODELS ====================
class ProductCreate(BaseModel):
    """Fields required to create a new product"""
    name: str
    slug: Optional[str] = None
    short_description: Optional[str] = None
    description: str
    price: float
    compare_at_price: Optional[float] = None
    currency: str = "ZAR"
    brand: Optional[str] = None
    sku: Optional[str] = None
    category: int
    image_url: Optional[HttpUrl] = None
    images: Optional[List[HttpUrl]] = None
    stock_quantity: int = 0
    availability_status: str = "in_stock"
    specifications: Optional[Dict[str, str]] = None
    weight_kg: Optional[float] = None
    is_active: bool = True
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

# ==================== TEST FUNCTIONS ====================

def test_pydantic_validation():
    """Test 1: Can Pydantic validate the data?"""
    print("\n" + "="*70)
    print("TEST 1: PYDANTIC VALIDATION")
    print("="*70)
    
    try:
        for idx, product_data in enumerate(SAMPLE_BULK_DATA):
            print(f"\nValidating product {idx + 1}...")
            product = ProductCreate(**product_data)
            print(f"✅ Product '{product.name}' passed validation")
            print(f"   - Price: {product.price}")
            print(f"   - Category: {product.category}")
            print(f"   - Images: {len(product.images) if product.images else 0}")
            print(f"   - Specs: {len(product.specifications) if product.specifications else 0} keys")
        
        print(f"\n✅ ALL PRODUCTS PASSED PYDANTIC VALIDATION")
        return True
    
    except Exception as e:
        print(f"\n❌ PYDANTIC VALIDATION FAILED")
        print(f"Error: {type(e).__name__}")
        print(f"Message: {str(e)}")
        return False


def test_mongodb_insert_format():
    """Test 2: What would the MongoDB documents look like?"""
    print("\n" + "="*70)
    print("TEST 2: MONGODB INSERT FORMAT")
    print("="*70)
    
    try:
        new_products = []
        for idx, product_data in enumerate(SAMPLE_BULK_DATA):
            product = ProductCreate(**product_data)
            
            # This is what gets inserted into MongoDB
            doc = {
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "category": product.category,
                "created_at": datetime.now(timezone.utc),
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
            }
            
            new_products.append(doc)
            
            print(f"\n📦 Product {idx + 1} MongoDB document:")
            print(f"   Name: {doc['name']}")
            print(f"   Price: {doc['price']}")
            print(f"   Specs: {doc['specifications']}")
            print(f"   Images: {doc['images']}")
        
        print(f"\n✅ MONGODB FORMAT LOOKS CORRECT")
        print(f"   Total products to insert: {len(new_products)}")
        return True
    
    except Exception as e:
        print(f"\n❌ MONGODB FORMAT ERROR")
        print(f"Error: {type(e).__name__}")
        print(f"Message: {str(e)}")
        return False


def test_json_serializable():
    """Test 3: Can the data be JSON serialized? (for API response)"""
    print("\n" + "="*70)
    print("TEST 3: JSON SERIALIZABILITY")
    print("="*70)
    
    try:
        new_products = []
        for product_data in SAMPLE_BULK_DATA:
            product = ProductCreate(**product_data)
            
            doc = {
                "id": "507f1f77bcf86cd799439011",  # Mock ObjectId
                "name": product.name,
                "price": product.price,
                "category": product.category,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            new_products.append(doc)
        
        response = {
            "success": True,
            "message": f"{len(new_products)} products created successfully!",
            "count": len(new_products),
            "products": new_products
        }
        
        json_str = json.dumps(response, indent=2, default=str)
        print(f"\n✅ DATA IS JSON SERIALIZABLE")
        print(f"   Response size: {len(json_str)} bytes")
        return True
    
    except Exception as e:
        print(f"\n❌ JSON SERIALIZATION ERROR")
        print(f"Error: {type(e).__name__}")
        print(f"Message: {str(e)}")
        return False


def test_mongodb_connection():
    """Test 4: Can we connect to MongoDB? (requires pymongo)"""
    print("\n" + "="*70)
    print("TEST 4: MONGODB CONNECTION")
    print("="*70)
    
    try:
        from pymongo import MongoClient
        import os
        
        MONGO_URI = os.getenv(
            "MONGO_URI",
            "mongodb+srv://SleepyDreams:saRqSb7xoc1cI1DO@kingburgercluster.ktvavv3.mongodb.net/?retryWrites=true&w=majority"
        )
        
        print(f"Connecting to MongoDB...")
        client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False, serverSelectionTimeoutMS=5000)
        
        # Try to access the database
        db = client["kingburgerstore_db"]
        products_collection = db["products"]
        
        # Try a simple operation
        count = products_collection.count_documents({})
        print(f"✅ MONGODB CONNECTION SUCCESSFUL")
        print(f"   Database: kingburgerstore_db")
        print(f"   Collection: products")
        print(f"   Current products in DB: {count}")
        
        client.close()
        return True
    
    except ImportError:
        print(f"⚠️  SKIP: pymongo not installed")
        return None
    except Exception as e:
        print(f"\n❌ MONGODB CONNECTION FAILED")
        print(f"Error: {type(e).__name__}")
        print(f"Message: {str(e)}")
        return False


# ==================== RUN ALL TESTS ====================

def run_all_tests():
    print("\n" + "#"*70)
    print("# BULK IMPORT DIAGNOSTIC TESTS")
    print("#"*70)
    
    results = {
        "Pydantic Validation": test_pydantic_validation(),
        "MongoDB Format": test_mongodb_insert_format(),
        "JSON Serializable": test_json_serializable(),
        "MongoDB Connection": test_mongodb_connection(),
    }
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⚠️  SKIP"
        print(f"{status} - {test_name}")
    
    print("\n" + "#"*70)
    print("# END DIAGNOSTIC TESTS")
    print("#"*70 + "\n")


if __name__ == "__main__":
    run_all_tests()