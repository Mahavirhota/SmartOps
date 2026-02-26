"""
Audit Logging — Track security-critical actions.

Architecture Decision:
Audit logs are immutable records of who did what, when, and where.
They are essential for compliance (SOC2, GDPR) and security forensics.
The model stores structured data including IP address, user agent,
and a JSON diff of changes.
"""
import logging
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    """
    Immutable audit log entry for security-critical actions.

    Tracks: logins, data changes, role changes, permission changes.
    Never delete audit logs — they are your compliance evidence.
    """

    class Action(models.TextChoices):
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        LOGIN_FAILED = 'login_failed', 'Login Failed'
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        ROLE_CHANGE = 'role_change', 'Role Change'
        PERMISSION_CHANGE = 'permission_change', 'Permission Change'
        EXPORT = 'export', 'Data Export'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    resource_type = models.CharField(
        max_length=100,
        help_text="Model/resource name (e.g., 'User', 'Organization')",
    )
    resource_id = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="ID of the affected resource.",
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON diff of old→new values for data changes.",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    tenant_id = models.CharField(max_length=100, blank=True, default='')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'core_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action'], name='idx_audit_user_action'),
            models.Index(fields=['resource_type', 'resource_id'], name='idx_audit_resource'),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.action} - {self.resource_type}"


def audit_action(
    user,
    action: str,
    resource_type: str,
    resource_id: str = '',
    changes: dict = None,
    request=None,
) -> AuditLog:
    """
    Helper to create an audit log entry.

    Usage:
        audit_action(
            user=request.user,
            action=AuditLog.Action.UPDATE,
            resource_type='Organization',
            resource_id=str(org.id),
            changes={'name': {'old': 'Acme', 'new': 'Acme Corp'}},
            request=request,
        )
    """
    ip_address = None
    user_agent = ''
    tenant_id = ''

    if request:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if hasattr(request, 'tenant') and request.tenant:
            tenant_id = str(request.tenant.id)

    log = AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes or {},
        ip_address=ip_address,
        user_agent=user_agent,
        tenant_id=tenant_id,
    )

    logger.info(
        f"Audit: {action} on {resource_type}({resource_id}) by {user}",
        extra={
            'audit_action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
        },
    )

    return log
