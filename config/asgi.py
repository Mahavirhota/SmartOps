"""
ASGI Configuration — Supports both HTTP and WebSocket protocols.

Django Channels uses ASGI to handle WebSocket connections alongside
traditional HTTP. The ProtocolTypeRouter dispatches based on protocol:
- HTTP → Standard Django views
- WebSocket → Channels consumers (with auth middleware)
"""
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.notifications.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
