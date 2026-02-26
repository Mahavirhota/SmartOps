"""
Notification Service — Creates notifications and dispatches via WebSocket.
"""
import logging
from typing import Optional

from django.contrib.auth import get_user_model

from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """Handles notification creation and real-time delivery."""

    @staticmethod
    def create_notification(
        title: str,
        message: str,
        notification_type: str = 'info',
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> Notification:
        """
        Create a notification and attempt real-time WebSocket delivery.

        Falls back gracefully if Channels is not running.
        """
        notification = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            data=data or {},
        )

        if user_id:
            notification.user_id = user_id
            # Derive tenant from user if not provided
            if not tenant_id:
                try:
                    user = User.objects.get(id=user_id)
                    if user.tenant_id:
                        notification.tenant_id = user.tenant_id
                except User.DoesNotExist:
                    pass

        if tenant_id:
            notification.tenant_id = tenant_id

        notification.save()

        # Attempt real-time delivery via WebSocket
        NotificationService._send_websocket(notification)

        return notification

    @staticmethod
    def _send_websocket(notification: Notification) -> None:
        """Send notification via WebSocket using Django Channels."""
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if not channel_layer:
                return

            # Determine the group to send to
            if notification.user_id:
                group_name = f"notifications_{notification.user_id}"
            elif notification.tenant_id:
                group_name = f"notifications_tenant_{notification.tenant_id}"
            else:
                return

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'notification.send',
                    'notification': {
                        'id': str(notification.id),
                        'type': notification.notification_type,
                        'title': notification.title,
                        'message': notification.message,
                        'data': notification.data,
                        'created_at': notification.created_at.isoformat()
                        if notification.created_at else None,
                    },
                }
            )

        except ImportError:
            logger.debug("Django Channels not installed, skipping WebSocket delivery")
        except Exception as e:
            logger.error(f"WebSocket delivery failed: {e}")

    @staticmethod
    def mark_as_read(notification_id: str, user) -> None:
        """Mark a notification as read."""
        from django.utils import timezone
        Notification.objects.filter(
            id=notification_id,
            user=user,
        ).update(is_read=True, read_at=timezone.now())
