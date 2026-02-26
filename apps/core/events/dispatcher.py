"""
Event Dispatcher — Routes domain events to Celery for async processing.

Architecture Decision:
Events are dispatched asynchronously via Celery to avoid blocking the
request cycle. This enables fire-and-forget semantics: the API responds
immediately while event handlers process in the background.
"""
import logging
from apps.core.events.base import DomainEvent

logger = logging.getLogger(__name__)


class EventDispatcher:
    """
    Dispatches domain events to Celery for asynchronous processing.
    
    Events are serialized and sent to the `process_domain_event` task,
    which handles retry logic, error handling, and dead letter routing.
    """

    @staticmethod
    def dispatch(event_type: str, payload: dict) -> DomainEvent:
        """
        Create and dispatch a domain event.
        
        Args:
            event_type: Type identifier (e.g., 'user_created')
            payload: Event-specific data
            
        Returns:
            The created DomainEvent instance
        """
        event = DomainEvent(event_type=event_type, payload=payload)

        logger.info(
            f"Dispatching event: {event_type}",
            extra={
                'event_id': event.event_id,
                'event_type': event_type,
            }
        )

        # Send to Celery for async processing
        from apps.core.tasks import process_domain_event
        process_domain_event.delay(event.to_dict())

        return event
