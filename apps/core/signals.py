"""
Signal handlers — Register event handlers and audit hooks on app startup.

This module is imported by CoreConfig.ready() to ensure all handlers
are registered when Django boots up.
"""
import logging

from apps.core.events.handlers import (handle_invoice_paid,
                                       handle_role_changed,
                                       handle_user_created,
                                       handle_workflow_completed)
from apps.core.events.registry import EventRegistry

logger = logging.getLogger(__name__)

# ── Register Domain Event Handlers ────────────────────────────────
# Each handler processes events asynchronously via Celery.
# Multiple handlers can be registered for the same event type.

EventRegistry.register('user_created', handle_user_created)
EventRegistry.register('invoice_paid', handle_invoice_paid)
EventRegistry.register('workflow_completed', handle_workflow_completed)
EventRegistry.register('role_changed', handle_role_changed)

logger.info("Domain event handlers registered successfully.")
