"""
Celery tasks for event processing with retry and dead letter handling.

Architecture Decision:
- Exponential backoff retry: prevents thundering herd on transient failures.
- Max retries: prevents infinite loops on permanent failures.
- Dead letter handling: failed events are stored for manual inspection and
  replay, ensuring no event is silently lost.
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)

# ── Event Processing ──────────────────────────────────────────────


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=10,
    acks_late=True,  # Acknowledge after processing (at-least-once delivery)
)
def process_domain_event(self, event_data: dict) -> None:
    """
    Process a domain event by routing it to registered handlers.

    Retry Strategy:
    - Exponential backoff: 10s, 20s, 40s, 80s, 160s
    - After max_retries, routes to dead letter handler

    This ensures transient failures (network, DB) are retried,
    while permanent failures are captured for investigation.
    """
    event_type = event_data.get('event_type', 'unknown')
    event_id = event_data.get('event_id', 'unknown')

    logger.info(
        f"Processing event: {event_type} (ID: {event_id})",
        extra={'event_id': event_id, 'event_type': event_type},
    )

    try:
        from apps.core.events.registry import EventRegistry
        handlers = EventRegistry.get_handlers(event_type)

        if not handlers:
            logger.warning(f"No handlers registered for event: {event_type}")
            return

        for handler in handlers:
            try:
                handler(event_data)
                logger.info(
                    f"Handler '{handler.__name__}' completed for event {event_id}"
                )
            except Exception as e:
                logger.error(
                    f"Handler '{handler.__name__}' failed for event {event_id}: {e}"
                )
                raise  # Re-raise to trigger task retry

    except Exception as exc:
        # Calculate exponential backoff
        retry_delay = self.default_retry_delay * (2 ** self.request.retries)

        if self.request.retries < self.max_retries:
            logger.warning(
                f"Retrying event {event_id} in {retry_delay}s "
                f"(attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            # Max retries exceeded — send to dead letter
            logger.error(
                f"Event {event_id} permanently failed after {self.max_retries} retries"
            )
            store_dead_letter.delay(event_data, str(exc))


@shared_task
def store_dead_letter(event_data: dict, error_message: str) -> None:
    """
    Store permanently failed events for manual investigation.

    Dead letters are stored in the database with the original event data
    and the error that caused the failure. Operations teams can review
    and replay these events after fixing the underlying issue.
    """
    from apps.core.models.dead_letter import DeadLetterEvent

    DeadLetterEvent.objects.create(
        event_type=event_data.get('event_type', 'unknown'),
        event_id=event_data.get('event_id', 'unknown'),
        payload=event_data,
        error_message=error_message,
    )

    logger.error(
        f"Dead letter stored: {event_data.get('event_type')} "
        f"(ID: {event_data.get('event_id')})"
    )
