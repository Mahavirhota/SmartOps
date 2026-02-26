"""
Tenant Middleware — Extracts tenant context from JWT for multi-tenant isolation.

Architecture Decision:
Using thread-local storage to propagate tenant context is a well-established
pattern for Django. It allows the TenantManager to access the current tenant
without passing it explicitly through every function call. This is safe because
Django processes each request in a single thread (or async context).

Flow:
1. JWT is decoded by SimpleJWT (already in request.user)
2. This middleware reads the user's organization (tenant)
3. Stores it in thread-local for ORM-level auto-filtering
"""
import threading
from typing import Optional
from django.http import HttpRequest, HttpResponse

_thread_locals = threading.local()


def get_current_tenant():
    """Get the current tenant from thread-local storage."""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant) -> None:
    """Set the current tenant in thread-local storage."""
    _thread_locals.tenant = tenant


def clear_current_tenant() -> None:
    """Clear the current tenant from thread-local storage."""
    _thread_locals.tenant = None


class TenantMiddleware:
    """
    Middleware that extracts tenant from the authenticated user's JWT
    and stores it in thread-local storage for automatic queryset filtering.
    
    Requires SimpleJWT authentication to run before this middleware.
    The tenant is determined by the user's active organization membership.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Clear tenant at the start of each request to prevent leakage
        clear_current_tenant()

        if hasattr(request, 'user') and request.user.is_authenticated:
            tenant = self._resolve_tenant(request)
            if tenant:
                set_current_tenant(tenant)
                request.tenant = tenant

        response = self.get_response(request)

        # Always clear after request is processed
        clear_current_tenant()
        return response

    def _resolve_tenant(self, request: HttpRequest) -> Optional[object]:
        """
        Resolve the tenant for the current request.
        
        Priority:
        1. X-Tenant-ID header (for multi-org users switching context)
        2. User's default organization (tenant_id on user model)
        """
        # Check for explicit tenant header
        tenant_id = request.META.get('HTTP_X_TENANT_ID')
        if tenant_id:
            from apps.organizations.models import Organization
            try:
                tenant = Organization.objects.get(
                    id=tenant_id,
                    members=request.user,
                    is_active=True
                )
                return tenant
            except Organization.DoesNotExist:
                return None

        # Fall back to user's default tenant
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return request.user.tenant

        return None
