"""Dead Letter Event model for storing permanently failed events."""
import uuid

from django.db import models


class DeadLetterEvent(models.Model):
    """
    Stores events that failed after all retries.

    Operations teams can review dead letters, fix the issue,
    and replay them using the stored payload.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100, db_index=True)
    event_id = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField(default=dict)
    error_message = models.TextField()
    is_replayed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    replayed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'core_dead_letter_event'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"DeadLetter: {self.event_type} ({self.event_id})"
