"""
Request ID Middleware — Generates a unique ID for every request.

Architecture Decision:
Request tracing is essential for production debugging. Each request gets a
UUID that propagates through logs, Sentry events, and response headers.
This enables correlating all log entries for a single user action across
services, workers, and databases.
"""
import uuid
import threading
from django.http import HttpRequest, HttpResponse

_thread_locals = threading.local()


def get_request_id() -> str:
    """Get the current request ID from thread-local storage."""
    return getattr(_thread_locals, 'request_id', 'no-request-id')


class RequestIDMiddleware:
    """
    Assigns a unique request ID to every incoming request.
    
    - Checks for existing X-Request-ID header (from load balancers/API gateways)
    - Generates a new UUID4 if none present
    - Stores in thread-local for logging injection
    - Adds to response headers for client-side correlation
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Reuse upstream request ID or generate new one
        request_id = request.META.get(
            'HTTP_X_REQUEST_ID',
            str(uuid.uuid4())
        )
        _thread_locals.request_id = request_id
        request.request_id = request_id

        response = self.get_response(request)
        response['X-Request-ID'] = request_id

        # Clean up thread-local
        _thread_locals.request_id = None
        return response
