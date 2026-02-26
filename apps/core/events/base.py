"""
Domain Event base class.

Architecture Decision:
Domain events decouple components. When something important happens
(user created, invoice paid), the originating code doesn't need to know
WHO cares about that event. It just emits it. Handlers are registered
separately, enabling loose coupling and easy extensibility.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class DomainEvent:
    """
    Base class for all domain events in SmartOps.

    Every event is immutable, timestamped, and uniquely identified.
    The payload is a flexible dict for event-specific data.
    """
    event_type: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event for Celery task transport."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'version': self.version,
        }
