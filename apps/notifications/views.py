"""Notification serializers and views."""
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .services import NotificationService


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id', 'notification_type', 'title', 'message',
            'data', 'is_read', 'read_at', 'created_at',
        )
        read_only_fields = fields


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """List and manage notifications for the authenticated user."""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or self.request.user.is_anonymous:
            return Notification.objects.none()
        return Notification.objects.filter(
            user=self.request.user,
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        """Mark a notification as read."""
        NotificationService.mark_as_read(pk, request.user)
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['post'])
    def read_all(self, request):
        """Mark all notifications as read."""
        from django.utils import timezone
        Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        return Response({'status': 'all marked as read'})
