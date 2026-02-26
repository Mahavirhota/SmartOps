"""Workflow serializers."""
from rest_framework import serializers
from .models import Workflow, WorkflowStep, WorkflowExecution


class WorkflowStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = ('id', 'name', 'step_type', 'order', 'config')


class WorkflowSerializer(serializers.ModelSerializer):
    steps = WorkflowStepSerializer(many=True, read_only=True)
    execution_count = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = (
            'id', 'name', 'description', 'status', 'trigger_event',
            'config', 'steps', 'execution_count', 'created_at',
        )
        read_only_fields = ('created_at',)

    def get_execution_count(self, obj: Workflow) -> int:
        return obj.executions.count()


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)

    class Meta:
        model = WorkflowExecution
        fields = (
            'id', 'workflow', 'workflow_name', 'status',
            'trigger_event', 'input_data', 'output_data',
            'error_message', 'started_at', 'completed_at',
        )
        read_only_fields = fields
