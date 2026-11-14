"""ASGI config for Pulse: Django HTTP and authenticated WebSockets."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from api.routing import websocket_urlpatterns
from api.websocket_auth import SupabaseJWTWebSocketMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        SupabaseJWTWebSocketMiddleware(URLRouter(websocket_urlpatterns))
    ),
})
