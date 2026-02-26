"""
Cache Service — Redis-backed caching with tenant-aware key prefixing.

Architecture Decision:
- Tenant-aware keys prevent cache pollution across tenants.
- Permission caching reduces DB hits for RBAC checks.
- TTL-based expiration ensures stale data is auto-purged.
- Decorator pattern for easy view-level caching.
"""
import json
import hashlib
import logging
import functools
from typing import Optional, Any
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Default cache TTLs (seconds)
CACHE_TTL_SHORT = 60          # 1 minute
CACHE_TTL_MEDIUM = 300        # 5 minutes
CACHE_TTL_LONG = 3600         # 1 hour
CACHE_TTL_PERMISSIONS = 600   # 10 minutes


class CacheService:
    """
    Centralized cache service with tenant isolation.
    All cache keys are prefixed with tenant_id to prevent cross-tenant leaks.
    """

    @staticmethod
    def _build_key(key: str, tenant_id: Optional[str] = None) -> str:
        """Build a cache key with optional tenant prefix."""
        if tenant_id:
            return f"smartops:{tenant_id}:{key}"
        return f"smartops:{key}"

    @staticmethod
    def get(key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """Get a value from cache."""
        full_key = CacheService._build_key(key, tenant_id)
        return cache.get(full_key)

    @staticmethod
    def set(
        key: str,
        value: Any,
        ttl: int = CACHE_TTL_MEDIUM,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Set a value in cache with TTL."""
        full_key = CacheService._build_key(key, tenant_id)
        cache.set(full_key, value, ttl)

    @staticmethod
    def delete(key: str, tenant_id: Optional[str] = None) -> None:
        """Delete a value from cache."""
        full_key = CacheService._build_key(key, tenant_id)
        cache.delete(full_key)

    @staticmethod
    def get_user_permissions(user_id: str) -> Optional[dict]:
        """Get cached permissions for a user."""
        return CacheService.get(f"permissions:{user_id}")

    @staticmethod
    def set_user_permissions(user_id: str, permissions: dict) -> None:
        """Cache user permissions."""
        CacheService.set(
            f"permissions:{user_id}",
            permissions,
            ttl=CACHE_TTL_PERMISSIONS,
        )

    @staticmethod
    def invalidate_user_permissions(user_id: str) -> None:
        """Invalidate cached permissions (e.g., after role change)."""
        CacheService.delete(f"permissions:{user_id}")
        logger.info(f"Invalidated permission cache for user {user_id}")


def cached_view(ttl: int = CACHE_TTL_MEDIUM, per_tenant: bool = True):
    """
    Decorator for caching DRF view responses.
    
    Usage:
        @cached_view(ttl=300, per_tenant=True)
        def list(self, request):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(view_instance, request, *args, **kwargs):
            # Build cache key from URL + query params
            cache_key_data = f"{request.path}:{request.query_params.urlencode()}"
            cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()

            tenant_id = None
            if per_tenant and hasattr(request, 'tenant') and request.tenant:
                tenant_id = str(request.tenant.id)

            # Try to get from cache
            cached = CacheService.get(f"view:{cache_key}", tenant_id)
            if cached is not None:
                from rest_framework.response import Response
                return Response(cached)

            # Execute view and cache result
            response = func(view_instance, request, *args, **kwargs)
            if response.status_code == 200:
                CacheService.set(
                    f"view:{cache_key}",
                    response.data,
                    ttl=ttl,
                    tenant_id=tenant_id,
                )

            return response
        return wrapper
    return decorator
