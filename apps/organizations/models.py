"""
Organization model — the tenant entity for multi-tenant isolation.

Architecture Decision:
- Organization is the tenant boundary. Every tenant-scoped resource
  references an Organization via FK.
- slug field for URL-friendly identifiers.
- JSONField settings for flexible per-tenant configuration.
- Membership model for M2M with role tracking per-org.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Organization(models.Model):
    """
    Represents a tenant (organization) in the multi-tenant architecture.
    All tenant-scoped data references this model via FK.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Membership',
        related_name='organizations',
    )
    is_active = models.BooleanField(default=True)
    settings_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible per-tenant configuration (feature flags, limits, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations_organization'
        indexes = [
            models.Index(fields=['slug'], name='idx_org_slug'),
            models.Index(fields=['is_active'], name='idx_org_active'),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Membership(models.Model):
    """
    Through model for Organization membership.
    Tracks per-organization role, allowing users to have different
    roles in different organizations.
    """

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations_membership'
        unique_together = ('user', 'organization')

    def __str__(self) -> str:
        return f"{self.user.email} - {self.organization.name} ({self.role})"
