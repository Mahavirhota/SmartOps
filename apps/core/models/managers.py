"""
Custom QuerySet managers for multi-tenant isolation.

Architecture Decision:
Using a custom manager instead of view-level filtering ensures that
tenant isolation is enforced at the ORM layer. Even if a developer
forgets to filter in a view, the manager will prevent cross-tenant leaks.
"""
from typing import Optional

from django.db import models


class TenantQuerySet(models.QuerySet):
    """QuerySet that can be filtered by tenant."""

    def for_tenant(self, tenant_id: Optional[str] = None) -> 'TenantQuerySet':
        """Filter queryset to only include records for the given tenant."""
        if tenant_id is None:
            from apps.core.middleware.tenant import get_current_tenant
            tenant = get_current_tenant()
            if tenant:
                tenant_id = str(tenant.id)
        if tenant_id:
            return self.filter(tenant_id=tenant_id)
        return self.none()  # Safety: return nothing if no tenant


class TenantManager(models.Manager):
    """
    Manager that auto-scopes queries to the current tenant.

    Usage in models:
        objects = TenantManager()  # All queries auto-filtered by tenant
        unscoped = models.Manager()  # Escape hatch for admin/system queries
    """

    def get_queryset(self) -> TenantQuerySet:
        return TenantQuerySet(self.model, using=self._db)

    def for_tenant(self, tenant_id: Optional[str] = None) -> TenantQuerySet:
        return self.get_queryset().for_tenant(tenant_id)
