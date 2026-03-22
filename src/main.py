"""
MAIN APPLICATION FILE

This module initializes and configures the FastAPI application with all necessary
middleware, routers, and lifecycle management for the cleaning services API.

Please ensure to review available helpers and utilities in other modules for database
interactions. (Notably in postgresqlDB.py, models.py, helpers.py & auth.py)
"""

import sys
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter


import ssl
import logging
logging.basicConfig(level=logging.INFO)

from cache_middleware import CacheControlMiddleware
from auth import router as auth_router
from routers.users import router as users_router
from routers.products import router as products_router
from orderCreation.orders import router as orders_router
from routers.webhook_main import router as webhook_router
from routers.password_generator import router as password_generator_router
from debug_router import debug_router

from payment_routers.payment import router as payment_router
from payment_routers.paypal_router import router as paypal_router

from databaseConnections.postgresqlDB import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    Logs application initialization details including Python and OpenSSL versions.
    """
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database init failed (non-blocking): {e}")
    print("🚀 Starting application...")
    print(f"🐍 Python version: {sys.version}")
    print(f"🔒 OpenSSL version: {ssl.OPENSSL_VERSION}")
    yield
    print("👋 Shutting down application...")


app = FastAPI(
    title="Kingburger's Store API",
    description="API for cleaning services booking and management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs"
)

print("✅ FastAPI app initialized")


# Middleware Configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = [
    "https://kingburger.site",
    "https://api.kingburger.site",
    "https://www.kingburger.site",
    "https://frontend-production-56ae.up.railway.app",
    "https://frontend.railway.internal:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
        "message": "Welcome to Kingburger's Store API! Visit /docs for API documentation.",
        "docs": "/docs",
        "version": "1.0.1"
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "kingburger's-store-api"
    }

# Router Registration
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(products_router)
app.include_router(payment_router)
app.include_router(orders_router)
app.include_router(password_generator_router)
app.include_router(webhook_router)
app.include_router(debug_router)
app.include_router(paypal_router)

print("✅ All routers registered")

