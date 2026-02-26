"""
Workflow Service — Business logic for workflow execution.
"""
from django.db import transaction
from django.utils import timezone

from .models import Workflow, WorkflowExecution


class WorkflowService:
    """Handles workflow execution orchestration."""

    @staticmethod
    @transaction.atomic
    def execute_workflow(
        workflow: Workflow,
        input_data: dict = None,
        triggered_by=None,
        trigger_event: str = '',
    ) -> WorkflowExecution:
        """
        Execute a workflow by creating an execution record
        and processing each step in order.
        """
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            tenant=workflow.tenant,
            status=WorkflowExecution.Status.RUNNING,
            triggered_by=triggered_by,
            trigger_event=trigger_event,
            input_data=input_data or {},
            started_at=timezone.now(),
        )

        try:
            steps = workflow.steps.all().order_by('order')
            step_results = []

            for step in steps:
                result = WorkflowService._execute_step(step, input_data or {})
                step_results.append({
                    'step': step.name,
                    'type': step.step_type,
                    'result': result,
                })

            execution.status = WorkflowExecution.Status.COMPLETED
            execution.output_data = {'steps': step_results}
            execution.completed_at = timezone.now()
            execution.save()

            # Dispatch completion event
            from apps.core.events.dispatcher import EventDispatcher
            EventDispatcher.dispatch('workflow_completed', {
                'workflow_id': str(workflow.id),
                'execution_id': str(execution.id),
                'tenant_id': str(workflow.tenant_id),
            })

        except Exception as e:
            execution.status = WorkflowExecution.Status.FAILED
            execution.error_message = str(e)
            execution.completed_at = timezone.now()
            execution.save()

        return execution

    @staticmethod
    def _execute_step(step, context: dict) -> dict:
        """Execute a single workflow step. Returns step output."""
        # Step execution is extensible — each step type can have
        # its own handler registered in a step handler registry.
        handlers = {
            'action': WorkflowService._handle_action,
            'condition': WorkflowService._handle_condition,
            'notification': WorkflowService._handle_notification,
            'delay': WorkflowService._handle_delay,
            'webhook': WorkflowService._handle_webhook,
        }

        handler = handlers.get(step.step_type, WorkflowService._handle_action)
        return handler(step, context)

    @staticmethod
    def _handle_action(step, context: dict) -> dict:
        return {'status': 'completed', 'action': step.config.get('action', 'default')}

    @staticmethod
    def _handle_condition(step, context: dict) -> dict:
        return {'status': 'evaluated', 'result': True}

    @staticmethod
    def _handle_notification(step, context: dict) -> dict:
        return {'status': 'sent', 'channel': step.config.get('channel', 'email')}

    @staticmethod
    def _handle_delay(step, context: dict) -> dict:
        return {'status': 'completed', 'delay': step.config.get('seconds', 0)}

    @staticmethod
    def _handle_webhook(step, context: dict) -> dict:
        return {'status': 'called', 'url': step.config.get('url', '')}
