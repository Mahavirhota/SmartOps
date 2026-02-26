"""
WebSocket Consumer for real-time notifications.

Architecture Decision:
Channels provides native WebSocket support for Django. Each user
connects to a personal notification group. When a background task
completes or an event fires, notifications are pushed in real-time
without polling.
"""
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time notification delivery.

    Clients connect to ws://host/ws/notifications/ with JWT auth.
    The consumer joins the user's personal notification group and
    the tenant-wide broadcast group.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')

        if not self.user or self.user.is_anonymous:
            await self.close(code=4001)
            return

        # Join user's personal group
        self.user_group = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name,
        )

        # Join tenant broadcast group
        if hasattr(self.user, 'tenant') and self.user.tenant:
            self.tenant_group = f"notifications_tenant_{self.user.tenant_id}"
            await self.channel_layer.group_add(
                self.tenant_group,
                self.channel_name,
            )

        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name,
            )
        if hasattr(self, 'tenant_group'):
            await self.channel_layer.group_discard(
                self.tenant_group,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        """Handle incoming messages (e.g., mark-as-read commands)."""
        action = content.get('action')

        if action == 'mark_read':
            notification_id = content.get('notification_id')
            if notification_id:
                from apps.notifications.services import NotificationService
                NotificationService.mark_as_read(notification_id, self.user)

    async def notification_send(self, event):
        """Send notification to the WebSocket client."""
        await self.send_json(event['notification'])
