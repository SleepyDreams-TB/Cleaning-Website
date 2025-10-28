"""
MAIN APPLICATION FILE
This is the entry point for your FastAPI application
All routes are organized in separate router files
"""

from fastapi import FastAPI
from fastapimiddlewarecors import CORSMiddleware
from contextlib import asynccontextmanager
import ssl
import sys
import os

# Import all routers
from auth import router as auth_router
from users import router as users_router
from products import router as products_router
from payment import router as payment_router
from orders import router as orders_router
from password_generator import router as password_generator_router

# ==================== FASTAPI LIFESPAN ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs when the app starts and shuts down
    Good place for startup/cleanup tasks
    """
    print("🚀 Starting application")
    print(f"🐍 Python version: {sysversion}")
    print(f"🔒 OpenSSL version: {sslOPENSSL_VERSION}")
    yield
    print("👋 Shutting down application")

# ==================== CREATE FASTAPI APP ====================
app = FastAPI(
    title="Cleaning Website API",
    description="API for cleaning services booking and management",
    version="100",
    lifespan=lifespan,
    docs_url="/docs"  # Swagger documentation at /docs
)

print("✅ FastAPI app initialized")

# ==================== CORS MIDDLEWARE ====================
# Allow these websites to access the API
allowed_origins = [
    "https://kingburgersite",
    "https://cleaning-website-static-siteonrendercom",
    "http://127001:5173",  # Local development
    "http://localhost:5173"    # Alternative local
]

appadd_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc)
    allow_headers=["*"],  # Allow all headers
)

print("✅ CORS middleware configured")

# ==================== BASIC ROUTES ====================
@appget("/")
def root():
    """Welcome endpoint - shows API is running"""
    return {
        "message": "Welcome to the Cleaning Website API! 🧹✨",
        "docs": "/docs",
        "version": "100"
    }

@appget("/health")
def health_check():
    """Health check endpoint - used by hosting services"""
    return {
        "status": "healthy",
        "service": "cleaning-website-api"
    }

# ==================== INCLUDE ALL ROUTERS ====================
# Each router handles a specific part of the application

appinclude_router(auth_router)           # /auth/* - login, register, logout
appinclude_router(users_router)          # /users/* - user profiles
appinclude_router(products_router)       # /products/* - cleaning products/services
appinclude_router(payment_router)        # /payments/* - payment processing
appinclude_router(orders_router)         # /orders/* - order management (SQL)
appinclude_router(password_generator_router)  # /password/* - password generator

print("✅ All routers registered")

# ==================== RUN SERVER ====================
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use 10000 as default
    port = int(osenvironget("PORT", 10000))
    
    print(f"🌐 Starting server on port {port}")
    
    uvicornrun(
        app,
        host="0000",  # Listen on all network interfaces
        port=port,
        reload=True      # Auto-reload on code changes (development only)
    )
