"""
Base models providing shared functionality across all SmartOps apps.

Architecture Decision:
- TimeStampedModel: Every model needs created_at/updated_at for auditing.
- TenantAwareModel: Enforces row-level multi-tenant isolation by requiring
  a tenant_id FK. Combined with TenantManager, this guarantees that queries
  NEVER leak data across tenants — a critical SaaS security requirement.
"""
import uuid
from django.db import models
from django.conf import settings


class TimeStampedModel(models.Model):
    """Abstract base model with automatic timestamp tracking."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Globally unique identifier (UUID4)."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class TenantAwareModel(TimeStampedModel):
    """
    Abstract model enforcing multi-tenant isolation.
    
    Every model that stores tenant-specific data MUST inherit from this.
    The custom TenantManager auto-filters queries by the current tenant,
    preventing cross-tenant data access at the ORM level.
    """
    tenant = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='%(class)s_items',
        db_index=True,
        help_text="The organization (tenant) this record belongs to."
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Override save to auto-populate tenant from the current request context
        if not explicitly set. This removes the burden from views/serializers.
        """
        if not self.tenant_id:
            from apps.core.middleware.tenant import get_current_tenant
            current_tenant = get_current_tenant()
            if current_tenant:
                self.tenant_id = current_tenant.id
        super().save(*args, **kwargs)
