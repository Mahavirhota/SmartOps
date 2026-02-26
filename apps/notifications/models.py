"""
Notification models — Tenant-aware notification system.
"""
from django.conf import settings
from django.db import models

from apps.core.models.base import TenantAwareModel


class Notification(TenantAwareModel):
    """
    Notification record for in-app and real-time notifications.
    Stored in DB for persistence; delivered in real-time via WebSocket.
    """

    class NotificationType(models.TextChoices):
        INFO = 'info', 'Info'
        SUCCESS = 'success', 'Success'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'
        WELCOME = 'welcome', 'Welcome'
        WORKFLOW_COMPLETE = 'workflow_complete', 'Workflow Complete'
        INVOICE = 'invoice', 'Invoice'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Target user. Null = broadcast to all tenant users.",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications_notification'
        indexes = [
            models.Index(fields=['user', 'is_read'], name='idx_notif_user_read'),
            models.Index(fields=['tenant', 'created_at'], name='idx_notif_tenant_created'),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.notification_type}: {self.title}"
