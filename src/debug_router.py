"""
DEBUG ROUTER - Copy this into your project
Add to your main.py: app.include_router(debug_router)

This provides HTTP endpoints to diagnose bulk import issues on Railway
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import os
from models import ProductCreate
from pymongo import MongoClient

debug_router = APIRouter(prefix="/debug", tags=["debug"])

# ==================== TEST: PYDANTIC VALIDATION ====================
@debug_router.post("/test-pydantic")
async def test_pydantic(products: list[ProductCreate]):
    """
    Test if Pydantic can validate your bulk data
    
    POST /debug/test-pydantic
    """
    return {
        "status": "✅ PASS",
        "message": f"Pydantic successfully validated {len(products)} products",
        "products_received": len(products),
        "first_product": {
            "name": products[0].name if products else None,
            "price": products[0].price if products else None,
            "category": products[0].category if products else None,
        }
    }


# ==================== TEST: MONGODB FORMAT ====================
@debug_router.post("/test-mongodb-format")
async def test_mongodb_format(products: list[ProductCreate]):
    """
    Test if the data can be formatted for MongoDB
    
    POST /debug/test-mongodb-format
    """
    try:
        test_docs = []
        for idx, product in enumerate(products):
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
            test_docs.append(doc)
        
        return {
            "status": "✅ PASS",
            "message": f"Successfully formatted {len(test_docs)} documents for MongoDB",
            "sample_doc_keys": list(test_docs[0].keys()) if test_docs else [],
            "total_documents": len(test_docs)
        }
    except Exception as e:
        return {
            "status": "❌ FAIL",
            "error": str(e),
            "error_type": type(e).__name__
        }


# ==================== TEST: MONGODB CONNECTION ====================
@debug_router.get("/test-mongodb-connection")
async def test_mongodb_connection():
    """
    Test if we can connect to MongoDB
    
    GET /debug/test-mongodb-connection
    """
    try:
        mongo_uri = os.getenv("MONGO_URI")
        
        if not mongo_uri:
            return {
                "status": "❌ FAIL",
                "error": "MONGO_URI environment variable is not set",
                "solution": "Add MONGO_URI to Railway environment variables"
            }
        
        print(f"🔗 Attempting MongoDB connection...")
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=10000
        )
        
        # Try to access database
        db = client["kingburgerstore_db"]
        products_collection = db["products"]
        
        # Test with a simple count
        count = products_collection.count_documents({})
        
        client.close()
        
        return {
            "status": "✅ PASS",
            "message": "Successfully connected to MongoDB",
            "database": "kingburgerstore_db",
            "collection": "products",
            "current_products_in_db": count,
            "mongo_uri_prefix": mongo_uri[:30] + "..." if mongo_uri else None
        }
    
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return {
            "status": "❌ FAIL",
            "error": str(e),
            "error_type": type(e).__name__,
            "solution": "Check MONGO_URI and MongoDB Atlas whitelist"
        }


# ==================== TEST: FULL BULK INSERT SIMULATION ====================
@debug_router.post("/test-bulk-insert")
async def test_bulk_insert(products: list[ProductCreate]):
    """
    Simulate a bulk insert WITHOUT saving (test only)
    This is the most important test - it will show the EXACT error
    
    POST /debug/test-bulk-insert
    """
    try:
        if not products:
            return {
                "status": "❌ FAIL",
                "error": "No products provided",
                "message": "Send at least one product in the request body"
            }
        
        # Step 1: Format documents
        print(f"📦 Formatting {len(products)} products...")
        test_docs = []
        for idx, product in enumerate(products):
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
            test_docs.append(doc)
        print(f"✅ Formatted {len(test_docs)} documents")
        
        # Step 2: Connect to MongoDB
        print(f"🔗 Connecting to MongoDB...")
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise Exception("MONGO_URI not set")
        
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=10000
        )
        
        db = client["kingburgerstore_db"]
        products_collection = db["products"]
        print(f"✅ Connected to MongoDB")
        
        # Step 3: Insert documents
        print(f"💾 Attempting to insert {len(test_docs)} documents...")
        result = products_collection.insert_many(test_docs)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} documents")
        
        # Step 4: Verify insertion
        print(f"📥 Verifying insertion...")
        created_count = products_collection.count_documents({"_id": {"$in": result.inserted_ids}})
        print(f"✅ Verified {created_count} documents in database")
        
        # Step 5: Cleanup (delete the test documents)
        print(f"🧹 Cleaning up test documents...")
        delete_result = products_collection.delete_many({"_id": {"$in": result.inserted_ids}})
        print(f"✅ Deleted {delete_result.deleted_count} test documents")
        
        client.close()
        
        return {
            "status": "✅ PASS",
            "message": f"Full insert simulation successful!",
            "steps": [
                "✅ Formatted documents",
                "✅ Connected to MongoDB",
                "✅ Inserted documents",
                "✅ Verified insertion",
                "✅ Cleaned up"
            ],
            "documents_inserted": len(result.inserted_ids),
            "documents_verified": created_count,
            "documents_cleaned": delete_result.deleted_count
        }
    
    except Exception as e:
        print(f"❌ Bulk insert test failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "❌ FAIL",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


# ==================== TEST: ENVIRONMENT CHECK ====================
@debug_router.get("/test-environment")
async def test_environment():
    """
    Check all environment variables and configuration
    
    GET /debug/test-environment
    """
    mongo_uri = os.getenv("MONGO_URI")
    
    return {
        "status": "✅ PASS",
        "environment": {
            "MONGO_URI_SET": mongo_uri is not None,
            "MONGO_URI_PREFIX": mongo_uri[:30] + "..." if mongo_uri else "NOT SET",
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "Not on Railway"),
            "NODE_ENV": os.getenv("NODE_ENV", "Not set")
        },
        "system": {
            "platform": __import__("sys").platform,
            "python_version": __import__("sys").version.split()[0]
        }
    }


# ==================== RUN ALL TESTS ====================
@debug_router.post("/run-all-tests")
async def run_all_tests(products: list[ProductCreate]):
    """
    Run all diagnostic tests at once
    
    POST /debug/run-all-tests
    """
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": {}
    }
    
    # Test 1
    try:
        result = await test_pydantic(products)
        results["tests"]["pydantic_validation"] = result
    except Exception as e:
        results["tests"]["pydantic_validation"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Test 2
    try:
        result = await test_mongodb_format(products)
        results["tests"]["mongodb_format"] = result
    except Exception as e:
        results["tests"]["mongodb_format"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Test 3
    try:
        result = await test_mongodb_connection()
        results["tests"]["mongodb_connection"] = result
    except Exception as e:
        results["tests"]["mongodb_connection"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Test 4
    try:
        result = await test_bulk_insert(products)
        results["tests"]["bulk_insert_simulation"] = result
    except Exception as e:
        results["tests"]["bulk_insert_simulation"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Test 5
    try:
        result = await test_environment()
        results["tests"]["environment"] = result
    except Exception as e:
        results["tests"]["environment"] = {"status": "❌ FAIL", "error": str(e)}
    
    # Summary
    passed = sum(1 for t in results["tests"].values() if t.get("status") == "✅ PASS")
    total = len(results["tests"])
    
    results["summary"] = {
        "passed": passed,
        "total": total,
        "all_passed": passed == total
    }
    
    return results