"""Billing serializers and views."""
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.middleware.tenant import get_current_tenant
from .models import Invoice, Subscription


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = (
            'id', 'invoice_number', 'amount', 'currency',
            'status', 'description', 'due_date', 'paid_at',
            'created_at',
        )
        read_only_fields = ('paid_at', 'created_at')


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', 'plan', 'status', 'starts_at', 'ends_at', 'created_at')
        read_only_fields = ('created_at',)


class InvoiceViewSet(viewsets.ModelViewSet):
    """CRUD for invoices, scoped to tenant."""
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or self.request.user.is_anonymous:
            return Invoice.objects.none()
        tenant = get_current_tenant()
        if not tenant:
            return Invoice.objects.none()
        return Invoice.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(tenant=tenant)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """Mark an invoice as paid."""
        invoice = self.get_object()
        invoice.mark_paid()
        return Response(InvoiceSerializer(invoice).data)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view for tenant subscriptions."""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or self.request.user.is_anonymous:
            return Subscription.objects.none()
        tenant = get_current_tenant()
        if not tenant:
            return Subscription.objects.none()
        return Subscription.objects.filter(tenant=tenant)
