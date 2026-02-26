"""
Workflow views — Thin controllers with tenant-aware querysets.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.middleware.tenant import get_current_tenant
from .models import Workflow, WorkflowExecution
from .serializers import WorkflowSerializer, WorkflowExecutionSerializer
from .services import WorkflowService


class WorkflowViewSet(viewsets.ModelViewSet):
    """CRUD for workflow definitions, scoped to the current tenant."""
    serializer_class = WorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or self.request.user.is_anonymous:
            return Workflow.objects.none()
        tenant = get_current_tenant()
        if not tenant:
            return Workflow.objects.none()
        return Workflow.objects.filter(
            tenant=tenant,
        ).prefetch_related('steps', 'executions')

    def perform_create(self, serializer):
        tenant = get_current_tenant()
        serializer.save(
            tenant=tenant,
            created_by=self.request.user,
        )

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Trigger a workflow execution."""
        workflow = self.get_object()
        execution = WorkflowService.execute_workflow(
            workflow=workflow,
            input_data=request.data.get('input_data', {}),
            triggered_by=request.user,
        )
        return Response(
            WorkflowExecutionSerializer(execution).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """List all executions of this workflow."""
        workflow = self.get_object()
        executions = workflow.executions.all().order_by('-created_at')[:50]
        serializer = WorkflowExecutionSerializer(executions, many=True)
        return Response(serializer.data)
