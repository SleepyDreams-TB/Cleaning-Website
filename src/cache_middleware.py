"""
Cache Control Middleware

Implements HTTP caching to improve API performance and reduce server load.
Responses are cached in the browser for specified durations based on endpoint type.

Cache Duration Strategy:
- Product endpoints: 10 minutes (relatively static content)
- Health checks: 1 minute (needs to be reasonably fresh)
- Root endpoint: 5 minutes (static welcome message)
- Auth/User endpoints: No caching (sensitive/dynamic data)
- Payment/Order endpoints: No caching (real-time data)
- Other GET endpoints: 2 minutes (safe default)
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timezone, timedelta


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        
        # Define endpoints that should NEVER be cached
        NO_CACHE_PATTERNS = [
            "/auth",
            "/users",
            "/payments",
            "/orders",
            "/dashboard",
            "/profile",
        ]
        
        if request.method == "GET":
            # Check if path matches any no-cache pattern
            should_not_cache = any(path.startswith(pattern) for pattern in NO_CACHE_PATTERNS)
            
            if should_not_cache:
                # Sensitive or real-time data - never cache
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            
            elif path.startswith("/products"):
                # Products - cache for 10 minutes
                response.headers["Cache-Control"] = "public, max-age=600"
                expiry_time = datetime.now(timezone.utc) + timedelta(minutes=10)
                response.headers["Expires"] = expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
            
            elif path == "/health":
                # Health check - cache for 1 minute
                response.headers["Cache-Control"] = "public, max-age=60"
            
            elif path == "/":
                # Root endpoint - cache for 5 minutes
                response.headers["Cache-Control"] = "public, max-age=300"
            
            else:
                # Default for other GET endpoints - cache for 2 minutes
                response.headers["Cache-Control"] = "public, max-age=120"
        
        return response


"""
──────────────────────────────────────────────────────────────────────
HTTP Cache Headers Reference
──────────────────────────────────────────────────────────────────────

Cache-Control Directives:

"public"
    Indicates the response can be cached by any cache (browser, CDN, proxy).
    Use for content that's the same for all users.

"private"
    Only the user's browser can cache, not shared caches.
    Use for user-specific but non-sensitive content.

"max-age=600"
    Response is considered fresh for 600 seconds (10 minutes).
    Browser won't make a new request until this time expires.

"no-cache"
    Browser must validate with server before using cached copy.
    Doesn't mean "don't cache" - means "check first".

"no-store"
    Response must not be stored anywhere - not even temporarily.
    Use for truly sensitive data (passwords, tokens, financial info).

"must-revalidate"
    Once cache expires, browser must check with server.
    Can't serve stale content even if offline.

Additional Headers:

"Expires"
    Absolute date/time when cache expires. Older method but still supported.
    Format: "Mon, 30 Oct 2025 14:30:00 GMT"

"Pragma: no-cache"
    Legacy header for HTTP/1.0 compatibility. Equivalent to "no-cache".

──────────────────────────────────────────────────────────────────────
How to Modify Cache Rules
──────────────────────────────────────────────────────────────────────

To Disable Cache for Specific Endpoints:
    Add the path pattern to NO_CACHE_PATTERNS list:
    
    NO_CACHE_PATTERNS = [
        "/auth",
        "/users",
        "/payments",
        "/orders",
        "/your-new-endpoint",  # Add here
    ]

To Add Custom Cache Duration:
    Add a new elif block with your endpoint and desired max-age:
    
    elif path.startswith("/products/featured"):
        response.headers["Cache-Control"] = "public, max-age=1800"  # 30 minutes

To Use Private Cache (user-specific):
    Replace "public" with "private":
    
    response.headers["Cache-Control"] = "private, max-age=300"

Common Cache Durations (in seconds):
    30 seconds:  max-age=30
    1 minute:    max-age=60
    5 minutes:   max-age=300
    10 minutes:  max-age=600
    30 minutes:  max-age=1800
    1 hour:      max-age=3600
    1 day:       max-age=86400

──────────────────────────────────────────────────────────────────────
Implementation Notes
──────────────────────────────────────────────────────────────────────

Performance Impact:
    First request to /products: Full server processing (~100-500ms)
    Subsequent requests: Served from browser cache (~5-10ms)
    This represents a 10-100x performance improvement for cached requests.

Security Considerations:
    Authentication and user-specific endpoints explicitly disable caching
    to prevent leaking sensitive information. Never cache data containing
    passwords, tokens, or personally identifiable information.
    
    Payment and order endpoints are never cached to ensure users always
    see the most current transaction status and order information.

Cache Invalidation:
    When product data is updated, users will see stale data until cache expires.
    Consider implementing cache-busting strategies:
    - Version-based URLs: /v1/products, /v2/products
    - Query parameters: /products?v=timestamp
    - Manual cache clearing instructions for admin users

Testing Cache Behavior:
    Browser DevTools > Network Tab:
    - Check Response Headers for "Cache-Control" directive
    - Status 200 (from cache) or "(disk cache)" indicates successful caching
    - Use "Disable cache" checkbox to test without caching
    - Shift+Reload forces fresh request bypassing cache

Monitoring:
    Track cache hit rates through server logs or APM tools.
    High cache hit rates (>80%) indicate effective caching strategy.
    Low hit rates may indicate cache duration is too short or data changes too frequently.

Best Practices:
    - Only cache GET requests (read operations)
    - Never cache POST/PUT/DELETE (write operations)
    - Use appropriate durations based on how often data changes
    - Balance freshness needs with performance gains
    - Document cache durations for team awareness

Common Pitfalls to Avoid:
    - Caching user-specific data with "public" directive
    - Setting max-age too high for frequently changing data
    - Forgetting to handle cache invalidation strategy
    - Not testing cache behavior in production-like environment
    - Caching payment or order data (security and accuracy concerns)

──────────────────────────────────────────────────────────────────────
"""