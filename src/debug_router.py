"""
DEBUG ROUTER - Diagnostic endpoints for troubleshooting bulk imports
This file provides HTTP endpoints to diagnose issues without external model dependencies
"""

from fastapi import APIRouter
from datetime import datetime, timezone
import os
import traceback
from typing import List

debug_router = APIRouter(prefix="/debug", tags=["debug"])


# ==================== TEST 1: Configuration ====================
@debug_router.get("/test-config")
async def test_config():
    """
    Check configuration and environment variables
    GET /debug/test-config
    """
    mongo_uri = os.getenv("MONGO_URI", "NOT SET")
    
    return {
        "status": "✅ PASS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "MONGO_URI_SET": mongo_uri != "NOT SET",
            "MONGO_URI_PREFIX": mongo_uri[:50] + "..." if mongo_uri != "NOT SET" else "NOT SET",
        },
        "available_endpoints": [
            "GET  /debug/test-config",
            "GET  /debug/test-mongodb",
            "POST /debug/test-single",
            "POST /debug/test-bulk",
            "POST /debug/run-all"
        ]
    }


# ==================== TEST 2: MongoDB Connection ====================
@debug_router.get("/test-mongodb")
async def test_mongodb():
    """
    Test MongoDB connection
    GET /debug/test-mongodb
    """
    try:
        from pymongo import MongoClient
        
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            return {
                "status": "❌ FAIL",
                "error": "MONGO_URI environment variable is not set",
                "solution": "Add MONGO_URI to your Railway environment variables"
            }
        
        print(f"🔗 Attempting MongoDB connection...")
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=10000
        )
        
        # Test connection with a simple operation
        db = client["kingburgerstore_db"]
        products_collection = db["products"]
        count = products_collection.count_documents({})
        
        client.close()
        
        return {
            "status": "✅ PASS",
            "message": "Successfully connected to MongoDB",
            "details": {
                "database": "kingburgerstore_db",
                "collection": "products",
                "current_products_in_db": count
            }
        }
    
    except ImportError as e:
        return {
            "status": "❌ FAIL",
            "error": "pymongo not installed",
            "solution": "Install pymongo: pip install pymongo"
        }
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        traceback.print_exc()
        return {
            "status": "❌ FAIL",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "solution": "Check MONGO_URI credentials and MongoDB Atlas IP whitelist"
        }


# ==================== TEST 3: Single Product ====================
@debug_router.post("/test-single")
async def test_single_product(product: dict):
    """
    Test creating a single product
    POST /debug/test-single
    
    Example body:
    {
        "name": "Test Product",
        "description": "Test description",
        "price": 100,
        "category": 1
    }
    """
    try:
        from pymongo import MongoClient
        
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            return {"status": "❌ FAIL", "error": "MONGO_URI not set"}
        
        # Validate required fields
        required_fields = ["name", "description", "price", "category"]
        for field in required_fields:
            if field not in product or not product[field]:
                return {
                    "status": "❌ FAIL",
                    "error": f"Missing required field: {field}"
                }
        
        print(f"📦 Testing single product: {product.get('name')}")
        
        # Connect
        client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=False, serverSelectionTimeoutMS=10000)
        db = client["kingburgerstore_db"]
        products_collection = db["products"]
        
        # Create document
        doc = {
            "name": product.get("name"),
            "description": product.get("description"),
            "price": product.get("price"),
            "category": product.get("category"),
            "created_at": datetime.now(timezone.utc),
            "is_active": product.get("is_active", True)
        }
        
        # Insert
        result = products_collection.insert_one(doc)
        inserted_id = str(result.inserted_id)
        print(f"✅ Inserted: {inserted_id}")
        
        # Delete immediately for cleanup
        products_collection.delete_one({"_id": result.inserted_id})
        print(f"✅ Cleaned up test document")
        
        client.close()
        
        return {
            "status": "✅ PASS",
            "message": "Single product insert test successful",
            "inserted_id": inserted_id,
            "product_name": product.get("name")
        }
    
    except Exception as e:
        print(f"❌ Single product test failed: {e}")
        traceback.print_exc()
        return {
            "status": "❌ FAIL",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }



# ==================== TEST 4: Bulk Import ====================
@debug_router.post("/test-bulk")
async def test_bulk_import(products: List[dict]):
    """
    Test bulk product import WITHOUT saving (diagnostic only)
    POST /debug/test-bulk
    
    This will format, insert, verify, and clean up test documents
    
    Example body:
    [
        {
            "name": "Product 1",
            "description": "Description",
            "price": 100,
            "category": 1
        }
    ]
    """
    try:
        from pymongo import MongoClient
        
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            return {"status": "❌ FAIL", "error": "MONGO_URI not set"}
        
        if not products or len(products) == 0:
            return {"status": "❌ FAIL", "error": "No products provided"}
        
        print(f"\n{'='*70}")
        print(f"📦 BULK IMPORT DIAGNOSTIC TEST")
        print(f"Testing {len(products)} products")
        print(f"{'='*70}")
        
        # Step 1: Validate and format
        print(f"\n1️⃣ Validating and formatting documents...")
        test_docs = []
        
        for idx, product in enumerate(products):
            print(f"   Product {idx + 1}: {product.get('name', 'UNNAMED')}")
            
            # Validate required fields
            required = ["name", "description", "price", "category"]
            for field in required:
                if field not in product or product[field] is None:
                    raise ValueError(f"Product {idx + 1}: Required field '{field}' is missing or null")
                if field == "name" and not str(product[field]).strip():
                    raise ValueError(f"Product {idx + 1}: 'name' cannot be empty")
                if field == "description" and not str(product[field]).strip():
                    raise ValueError(f"Product {idx + 1}: 'description' cannot be empty")
                if field == "price" and (not isinstance(product[field], (int, float)) or product[field] < 0):
                    raise ValueError(f"Product {idx + 1}: 'price' must be a positive number")
                if field == "category" and not isinstance(product[field], int):
                    raise ValueError(f"Product {idx + 1}: 'category' must be an integer")
            
            # Create document
            doc = {
                "name": product.get("name"),
                "description": product.get("description"),
                "price": product.get("price"),
                "category": product.get("category"),
                "created_at": datetime.now(timezone.utc),
                # Optional fields
                "slug": product.get("slug"),
                "short_description": product.get("short_description"),
                "compare_at_price": product.get("compare_at_price"),
                "currency": product.get("currency", "ZAR"),
                "brand": product.get("brand"),
                "sku": product.get("sku"),
                "image_url": str(product.get("image_url")) if product.get("image_url") else None,
                "images": [str(img) for img in product.get("images", [])] if product.get("images") else None,
                "stock_quantity": product.get("stock_quantity", 0),
                "availability_status": product.get("availability_status", "in_stock"),
                "specifications": product.get("specifications"),
                "weight_kg": product.get("weight_kg"),
                "is_active": product.get("is_active", True),
                "tags": product.get("tags"),
                "meta_title": product.get("meta_title"),
                "meta_description": product.get("meta_description"),
            }
            test_docs.append(doc)
        
        print(f"✅ Formatted {len(test_docs)} documents successfully")
        
        # Step 2: Connect to MongoDB
        print(f"\n2️⃣ Connecting to MongoDB...")
        client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=False, serverSelectionTimeoutMS=10000)
        db = client["kingburgerstore_db"]
        products_collection = db["products"]
        print(f"✅ Connected to MongoDB")
        
        # Step 3: Insert documents
        print(f"\n3️⃣ Inserting {len(test_docs)} documents...")
        insert_result = products_collection.insert_many(test_docs)
        print(f"✅ Insert successful! Inserted {len(insert_result.inserted_ids)} documents")
        
        # Step 4: Verify insertion
        print(f"\n4️⃣ Verifying insertion...")
        verify_count = products_collection.count_documents({"_id": {"$in": insert_result.inserted_ids}})
        print(f"✅ Verified {verify_count} documents in database")
        
        # Step 5: Cleanup
        print(f"\n5️⃣ Cleaning up test documents...")
        delete_result = products_collection.delete_many({"_id": {"$in": insert_result.inserted_ids}})
        print(f"✅ Deleted {delete_result.deleted_count} test documents")
        
        client.close()
        
        print(f"\n{'='*70}")
        print(f"✨ BULK IMPORT TEST PASSED - Your bulk import should work!")
        print(f"{'='*70}\n")
        
        return {
            "status": "✅ PASS",
            "message": "Bulk import test successful! Your bulk import endpoint should work.",
            "steps": [
                "✅ Validated and formatted documents",
                "✅ Connected to MongoDB",
                "✅ Inserted documents",
                "✅ Verified insertion",
                "✅ Cleaned up"
            ],
            "summary": {
                "products_tested": len(products),
                "documents_inserted": len(insert_result.inserted_ids),
                "documents_verified": verify_count,
                "documents_cleaned": delete_result.deleted_count
            }
        }
    
    except ValueError as ve:
        print(f"\n❌ VALIDATION ERROR: {ve}\n")
        return {
            "status": "❌ FAIL",
            "error_type": "Validation Error",
            "error": str(ve),
            "message": "Check your product data format"
        }
    
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ BULK IMPORT TEST FAILED")
        print(f"{'='*70}")
        print(f"Error: {e}\n")
        traceback.print_exc()
        print(f"{'='*70}\n")
        
        return {
            "status": "❌ FAIL",
            "error_type": type(e).__name__,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Check MongoDB connection and database settings"
        }


# ==================== TEST 5: Run All Tests ====================
@debug_router.post("/run-all")
async def run_all_tests(products: list = None):
    """
    Run all diagnostic tests
    POST /debug/run-all
    
    Optional: include products array to test bulk import
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": {}
    }
    
    # Test 1: Config
    try:
        config_result = await test_config()
        results["tests"]["configuration"] = config_result
    except Exception as e:
        results["tests"]["configuration"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Test 2: MongoDB
    try:
        mongo_result = await test_mongodb()
        results["tests"]["mongodb_connection"] = mongo_result
    except Exception as e:
        results["tests"]["mongodb_connection"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Test 3: Single Product
    if products:
        try:
            single_result = await test_single_product({"name": "Test", "description": "Test", "price": 100, "category": 1})
            results["tests"]["single_product"] = single_result
        except Exception as e:
            results["tests"]["single_product"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Test 4: Bulk Import
    if products:
        try:
            bulk_result = await test_bulk_import(products)
            results["tests"]["bulk_import"] = bulk_result
        except Exception as e:
            results["tests"]["bulk_import"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Summary
    passed = sum(1 for test in results["tests"].values() if test.get("status") == "✅ PASS")
    total = len(results["tests"])
    
    results["summary"] = {
        "tests_run": total,
        "tests_passed": passed,
        "tests_failed": total - passed,
        "all_passed": passed == total
    }
    
    return results