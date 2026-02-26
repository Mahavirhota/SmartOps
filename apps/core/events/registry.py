"""
Event Registry — Maps event types to their handlers.

Architecture Decision:
Handlers are registered declaratively, making it easy to add new
event reactions without modifying existing code (Open/Closed Principle).
"""
import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


class EventRegistry:
    """
    Registry mapping event types to handler functions.

    Usage:
        EventRegistry.register('user_created', send_welcome_email)
        EventRegistry.register('user_created', provision_default_workspace)

    Multiple handlers can be registered for the same event type.
    """
    _handlers: Dict[str, List[Callable]] = {}

    @classmethod
    def register(cls, event_type: str, handler: Callable) -> None:
        """Register a handler for an event type."""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
        logger.info(
            f"Registered handler '{handler.__name__}' for event '{event_type}'"
        )

    @classmethod
    def get_handlers(cls, event_type: str) -> List[Callable]:
        """Get all handlers for an event type."""
        return cls._handlers.get(event_type, [])

    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (useful for testing)."""
        cls._handlers = {}
