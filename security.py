from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import re

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.request_history = {
            ip: times for ip, times in self.request_history.items()
            if any(t > current_time - 60 for t in times)
        }
        
        # Check rate limit
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        self.request_history[client_ip] = [
            t for t in self.request_history[client_ip]
            if t > current_time - 60
        ]
        
        if len(self.request_history[client_ip]) >= self.requests_per_minute:
            return Response(
                content={"error": "Rate limit exceeded"},
                status_code=429,
                media_type="application/json"
            )
        
        self.request_history[client_ip].append(current_time)
        
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.request_history[client_ip])
        )
        
        return response
    
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Standard Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # FINAL CSP POLICY
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://unpkg.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            # This line fixes the 'connect-src' error for the .map files
            "connect-src 'self' https://unpkg.com https://cdn.jsdelivr.net;"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response

def setup_middleware(app):
    """Setup all middleware"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)