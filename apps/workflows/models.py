"""
Workflow models — Tenant-aware workflow definitions and execution tracking.

Architecture Decision:
- Workflow: Defines an automation template scoped to a tenant.
- WorkflowStep: Individual steps within a workflow (ordered).
- WorkflowExecution: Tracks each run of a workflow with status and output.

All models inherit TenantAwareModel for automatic multi-tenant isolation.
JSONField is used for flexible step config and execution output, allowing
different workflow types without schema changes.
"""
from django.db import models
from django.conf import settings
from apps.core.models.base import TenantAwareModel


class Workflow(TenantAwareModel):
    """
    A workflow template defining an automated process.
    Scoped to a tenant via TenantAwareModel.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        ARCHIVED = 'archived', 'Archived'

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    trigger_event = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Domain event that triggers this workflow (e.g., 'invoice_paid')."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_workflows',
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible workflow configuration."
    )

    class Meta:
        db_table = 'workflows_workflow'
        indexes = [
            models.Index(fields=['tenant', 'status'], name='idx_wf_tenant_status'),
            models.Index(fields=['trigger_event'], name='idx_wf_trigger'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"


class WorkflowStep(TenantAwareModel):
    """
    Individual step within a workflow.
    Steps are executed in order during workflow execution.
    """

    class StepType(models.TextChoices):
        ACTION = 'action', 'Action'
        CONDITION = 'condition', 'Condition'
        NOTIFICATION = 'notification', 'Notification'
        DELAY = 'delay', 'Delay'
        WEBHOOK = 'webhook', 'Webhook'

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='steps',
    )
    name = models.CharField(max_length=255)
    step_type = models.CharField(
        max_length=20,
        choices=StepType.choices,
        default=StepType.ACTION,
    )
    order = models.PositiveIntegerField(default=0)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Step-specific configuration (action params, conditions, etc.)."
    )

    class Meta:
        db_table = 'workflows_step'
        ordering = ['order']

    def __str__(self) -> str:
        return f"Step {self.order}: {self.name}"


class WorkflowExecution(TenantAwareModel):
    """
    Tracks a single execution (run) of a workflow.
    Records status, input/output, and timing for observability.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='executions',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    trigger_event = models.CharField(max_length=100, blank=True, default='')
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'workflows_execution'
        indexes = [
            models.Index(fields=['workflow', 'status'], name='idx_exec_wf_status'),
        ]

    def __str__(self) -> str:
        return f"Execution of {self.workflow.name}: {self.status}"
