"""
User model with RBAC and multi-tenant support.

Architecture Decision:
- Custom User model extending AbstractUser with email as the primary identifier.
- Role field with hierarchical choices (OWNER > ADMIN > MEMBER > VIEWER).
- tenant FK links user to their active organization for auto-scoping.
- UUID primary key for distributed-system compatibility.
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with multi-tenant and RBAC support.

    The tenant field represents the user's currently active organization.
    Users can belong to multiple organizations but operate within one
    tenant context at a time (switched via X-Tenant-ID header).
    """

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        VIEWER = 'viewer', 'Viewer'

    # Role hierarchy for permission checks (higher = more privileged)
    ROLE_HIERARCHY = {
        Role.OWNER: 4,
        Role.ADMIN: 3,
        Role.MEMBER: 2,
        Role.VIEWER: 1,
    }

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text="User's role within their active tenant."
    )
    tenant = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_users',
        help_text="The user's currently active organization (tenant)."
    )
    phone = models.CharField(max_length=20, blank=True, default='')
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users_user'
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['tenant'], name='idx_user_tenant'),
        ]

    def __str__(self) -> str:
        return self.email

    def has_role_level(self, required_role: str) -> bool:
        """Check if user's role meets or exceeds the required role level."""
        user_level = self.ROLE_HIERARCHY.get(self.role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level
