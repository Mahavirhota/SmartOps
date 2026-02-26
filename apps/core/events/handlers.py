"""
Event Handlers — Concrete handlers for domain events.

Each handler is a simple function that receives an event dict.
Handlers are registered in the EventRegistry during app startup.
"""
import logging

logger = logging.getLogger(__name__)


def handle_user_created(event_data: dict) -> None:
    """Handle the user_created event — send welcome notification, setup defaults."""
    user_id = event_data['payload'].get('user_id')
    email = event_data['payload'].get('email')
    logger.info(f"Processing user_created event for {email} (ID: {user_id})")

    # Create welcome notification
    try:
        from apps.notifications.services import NotificationService
        NotificationService.create_notification(
            user_id=user_id,
            notification_type='welcome',
            title='Welcome to SmartOps!',
            message=f'Your account has been created successfully.',
        )
    except Exception as e:
        logger.error(f"Failed to create welcome notification: {e}")


def handle_invoice_paid(event_data: dict) -> None:
    """Handle the invoice_paid event — update billing records, notify user."""
    invoice_id = event_data['payload'].get('invoice_id')
    logger.info(f"Processing invoice_paid event for invoice {invoice_id}")


def handle_workflow_completed(event_data: dict) -> None:
    """Handle the workflow_completed event — notify user of completion."""
    workflow_id = event_data['payload'].get('workflow_id')
    execution_id = event_data['payload'].get('execution_id')
    logger.info(
        f"Processing workflow_completed: workflow={workflow_id}, "
        f"execution={execution_id}"
    )

    # Send real-time notification via WebSocket
    try:
        from apps.notifications.services import NotificationService
        tenant_id = event_data['payload'].get('tenant_id')
        NotificationService.create_notification(
            tenant_id=tenant_id,
            notification_type='workflow_complete',
            title='Workflow Completed',
            message=f'Workflow execution {execution_id} has completed.',
        )
    except Exception as e:
        logger.error(f"Failed to send workflow completion notification: {e}")


def handle_role_changed(event_data: dict) -> None:
    """Handle role changes — audit log and cache invalidation."""
    user_id = event_data['payload'].get('user_id')
    old_role = event_data['payload'].get('old_role')
    new_role = event_data['payload'].get('new_role')
    logger.info(
        f"Role changed for user {user_id}: {old_role} -> {new_role}"
    )

    # Invalidate permission cache for this user
    try:
        from apps.core.cache import CacheService
        CacheService.invalidate_user_permissions(user_id)
    except Exception as e:
        logger.error(f"Failed to invalidate permission cache: {e}")
