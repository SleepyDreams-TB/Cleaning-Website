"""
MAIN APPLICATION FILE

This module initializes and configures the FastAPI application with all necessary
middleware, routers, and lifecycle management for the cleaning services API.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import ssl

from cache_middleware import CacheControlMiddleware
from auth import router as auth_router
from users import router as users_router
from products import router as products_router
from payment import router as payment_router
from orders import router as orders_router
from password_generator import router as password_generator_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Logs application initialization details including Python and OpenSSL versions.
    """
    print("🚀 Starting application...")
    print(f"🐍 Python version: {sys.version}")
    print(f"🔒 OpenSSL version: {ssl.OPENSSL_VERSION}")
    yield
    print("👋 Shutting down application...")


app = FastAPI(
    title="Cleaning Website API",
    description="API for cleaning services booking and management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs"
)

print("✅ FastAPI app initialized")


# Middleware Configuration
allowed_origins = [
    "https://kingburger.site",
    "https://api.kingburger.site",
    "https://sparkle-clean-app.onrender.com",
    "https://cleaning-website-g62w.onrender.com",
    "https://www.kingburger.site",
    "https://www.sparkle-clean-app.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origins],  # For development; replace with allowed_origins in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

print("✅ CORS middleware configured")

app.add_middleware(CacheControlMiddleware)
print("✅ Cache Control middleware configured")


@app.get("/")
def root():
    """Root endpoint returning API metadata and documentation link."""
    return {
        "message": "Welcome to the Cleaning Website API! Visit /docs for API documentation.",
        "docs": "/docs",
        "version": "1.0.1"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "cleaning-website-api"
    }


# Router Registration
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(payment_router)
app.include_router(orders_router)
app.include_router(password_generator_router)

print("✅ All routers registered")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Starting server on port {port}...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
        # reload=True removed for production
    )
