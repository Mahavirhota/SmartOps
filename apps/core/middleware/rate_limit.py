"""
Redis-based Rate Limiting Middleware — Sliding window algorithm.

Architecture Decision:
Rate limiting at the middleware level protects ALL endpoints uniformly.
The sliding window algorithm provides smoother rate limiting than
fixed windows (no burst at window boundaries).

Configurable per-endpoint or global limits via settings.
"""
import logging
import time

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Default: 100 requests per minute
DEFAULT_RATE_LIMIT = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)
DEFAULT_WINDOW = getattr(settings, 'RATE_LIMIT_WINDOW', 60)  # seconds


class RateLimitMiddleware:
    """
    Sliding window rate limiter using Redis sorted sets.

    Each request is timestamped and added to a sorted set keyed by
    the client's IP. Expired entries are pruned on each check.
    """

    # Paths exempt from rate limiting (health checks, metrics, etc.)
    EXEMPT_PATHS = ['/health', '/metrics', '/admin/']

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        # Skip rate limiting for exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return self.get_response(request)

        client_key = self._get_client_key(request)

        if self._is_rate_limited(client_key):
            logger.warning(
                f"Rate limited: {client_key} on {request.path}",
                extra={'client_key': client_key, 'path': request.path},
            )
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'detail': f'Maximum {DEFAULT_RATE_LIMIT} requests per {DEFAULT_WINDOW} seconds.',
                },
                status=429,
            )

        return self.get_response(request)

    def _get_client_key(self, request) -> str:
        """Build a rate limit key from client IP and authenticated user."""
        # Prefer authenticated user ID over IP for better accuracy
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"ratelimit:user:{request.user.id}"

        # Fall back to IP address
        ip = self._get_client_ip(request)
        return f"ratelimit:ip:{ip}"

    def _get_client_ip(self, request) -> str:
        """Extract client IP, respecting proxy headers."""
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def _is_rate_limited(self, key: str) -> bool:
        """Check if the client has exceeded the rate limit."""
        try:
            import redis as redis_lib
            r = redis_lib.from_url(
                getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            )

            now = time.time()
            window_start = now - DEFAULT_WINDOW

            pipe = r.pipeline()
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Count requests in window
            pipe.zcard(key)
            # Set expiry on the key itself
            pipe.expire(key, DEFAULT_WINDOW)
            results = pipe.execute()

            request_count = results[2]
            return request_count > DEFAULT_RATE_LIMIT

        except Exception as e:
            # If Redis is down, fail open (allow request)
            logger.error(f"Rate limit check failed: {e}")
            return False
