"""Rate limiting middleware for API requests.

Implements rate limiting using Redis as the backend storage.
Supports dynamic rate limits based on API key configuration.
"""

import time
from typing import Optional, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis backend.
    
    Supports two types of rate limiting:
    1. API Key-based: Uses the API key's configured rate_limit
    2. JWT-based: Uses default rate limit from settings
    
    Rate limit window is 1 minute.
    Headers added to responses:
    - X-RateLimit-Limit: Maximum requests allowed
    - X-RateLimit-Remaining: Remaining requests in current window
    - X-RateLimit-Reset: Unix timestamp when limit resets
    """
    
    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis: Optional[Redis] = None
        self.default_rate = settings.RATE_LIMIT_DEFAULT
        
    async def startup(self):
        """Initialize Redis connection."""
        try:
            self.redis = Redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.error("Failed to connect to Redis for rate limiting", error=str(e))
            self.redis = None
    
    def get_rate_limit_key(self, request: Request, rate_limit: int) -> Tuple[str, str]:
        """Generate Redis key and window identifier for rate limiting.
        
        Args:
            request: FastAPI request
            rate_limit: Requests per minute limit
            
        Returns:
            Tuple of (redis_key, window_key)
        """
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        
        if api_key:
            # Use API key prefix as identifier
            key_id = api_key[:12] if len(api_key) >= 12 else api_key
            return f"ratelimit:apikey:{key_id}", key_id
        else:
            # Fall back to IP address or JWT user
            # Try to get from auth header
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                # Use a hash of the token to avoid storing full tokens
                import hashlib
                token_hash = hashlib.sha256(auth_header[7:].encode()).hexdigest()[:16]
                key_id = f"jwt:{token_hash}"
            else:
                # Use IP address as fallback
                forwarded = request.headers.get("X-Forwarded-For")
                if forwarded:
                    key_id = forwarded.split(",")[0].strip()
                else:
                    key_id = request.client.host if request.client else "unknown"
                    key_id = f"ip:{key_id}"
            
            return f"ratelimit:{key_id}", key_id
    
    async def check_rate_limit(
        self, 
        request: Request, 
        rate_limit: int
    ) -> Tuple[bool, int, int, int]:
        """Check if request is within rate limit.
        
        Args:
            request: FastAPI request
            rate_limit: Maximum requests per minute
            
        Returns:
            Tuple of (allowed, remaining, limit, reset_time)
        """
        if not self.redis:
            # Redis not available - allow request
            return True, rate_limit, rate_limit, int(time.time()) + 60
        
        redis_key, key_id = self.get_rate_limit_key(request, rate_limit)
        
        # Use sliding window with Redis sorted set
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        pipe = self.redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(redis_key)
        
        # Add current request
        pipe.zadd(redis_key, {str(now): now})
        
        # Set expiration
        pipe.expire(redis_key, 60)
        
        results = await pipe.execute()
        current_count = results[1]
        
        # Check if over limit
        if current_count > rate_limit:
            # Remove the request we just added (it was over limit)
            await self.redis.zrem(redis_key, str(now))
            
            # Get oldest request to calculate reset time
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            if oldest:
                reset_time = int(oldest[0][1]) + 60
            else:
                reset_time = int(now) + 60
            
            return False, 0, rate_limit, reset_time
        
        remaining = rate_limit - current_count
        oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
        if oldest:
            reset_time = int(oldest[0][1]) + 60
        else:
            reset_time = int(now) + 60
        
        return True, remaining, rate_limit, reset_time
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Initialize Redis if not already done
        if self.redis is None:
            await self.startup()
        
        # Get rate limit from API key if present
        rate_limit = self.default_rate
        api_key = request.headers.get("X-API-Key")
        
        if api_key and self.redis:
            # Look up API key rate limit from database (cached in Redis)
            try:
                cache_key = f"apikey:config:{api_key[:12]}"
                cached_limit = await self.redis.get(cache_key)
                if cached_limit:
                    rate_limit = int(cached_limit)
            except Exception:
                pass
        
        # Check rate limit
        allowed, remaining, limit, reset_time = await self.check_rate_limit(
            request, rate_limit
        )
        
        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                key=self.get_rate_limit_key(request, rate_limit)[1],
                limit=limit,
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": str(reset_time - int(time.time())),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Simplified rate limiting middleware for testing/development.
    
    Uses in-memory storage instead of Redis. Not suitable for production
    with multiple server instances.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = {}  # {key: [(timestamp, count)]}
        self.default_rate = settings.RATE_LIMIT_DEFAULT
    
    async def dispatch(self, request: Request, call_next):
        """Process request with simple in-memory rate limiting."""
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get identifier
        api_key = request.headers.get("X-API-Key")
        if api_key:
            key = f"api:{api_key[:12]}"
        else:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                import hashlib
                key = f"jwt:{hashlib.sha256(auth[7:].encode()).hexdigest()[:16]}"
            else:
                client_ip = request.client.host if request.client else "unknown"
                key = f"ip:{client_ip}"
        
        now = time.time()
        window_start = now - 60
        
        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                (ts, count) for ts, count in self.requests[key] 
                if ts > window_start
            ]
        else:
            self.requests[key] = []
        
        # Count current requests
        total_count = sum(count for ts, count in self.requests[key])
        
        # Check limit
        if total_count >= self.default_rate:
            oldest_ts = min(ts for ts, _ in self.requests[key]) if self.requests[key] else now
            reset_time = int(oldest_ts + 60)
            
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": str(reset_time - int(now)),
                    "X-RateLimit-Limit": str(self.default_rate),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                }
            )
        
        # Record request
        self.requests[key].append((now, 1))
        
        # Process request
        response = await call_next(request)
        
        # Add headers
        new_total = sum(count for ts, count in self.requests[key])
        remaining = max(0, self.default_rate - new_total)
        reset_time = int(now + 60)
        
        response.headers["X-RateLimit-Limit"] = str(self.default_rate)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
