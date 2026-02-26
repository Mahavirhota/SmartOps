"""
Billing models — Invoice and subscription tracking.
All models are tenant-aware for multi-tenant isolation.
"""
from django.db import models
from django.conf import settings
from apps.core.models.base import TenantAwareModel


class Invoice(TenantAwareModel):
    """Invoice record for a tenant."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        OVERDUE = 'overdue', 'Overdue'
        CANCELLED = 'cancelled', 'Cancelled'

    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    description = models.TextField(blank=True, default='')
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'billing_invoice'
        indexes = [
            models.Index(fields=['tenant', 'status'], name='idx_invoice_tenant_status'),
        ]

    def __str__(self) -> str:
        return f"Invoice {self.invoice_number}: {self.amount} {self.currency}"

    def mark_paid(self) -> None:
        """Mark invoice as paid and dispatch event."""
        from django.utils import timezone
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at', 'updated_at'])

        from apps.core.events.dispatcher import EventDispatcher
        EventDispatcher.dispatch('invoice_paid', {
            'invoice_id': str(self.id),
            'invoice_number': self.invoice_number,
            'amount': str(self.amount),
            'tenant_id': str(self.tenant_id),
        })


class Subscription(TenantAwareModel):
    """Subscription plan tracking for a tenant."""

    class Plan(models.TextChoices):
        FREE = 'free', 'Free'
        STARTER = 'starter', 'Starter'
        PROFESSIONAL = 'professional', 'Professional'
        ENTERPRISE = 'enterprise', 'Enterprise'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'
        TRIAL = 'trial', 'Trial'

    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'billing_subscription'

    def __str__(self) -> str:
        return f"{self.tenant.name}: {self.plan} ({self.status})"
