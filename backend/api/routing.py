from django.urls import path

from .secure_consumers import SecureChatConsumer

websocket_urlpatterns = [
    path("api/", SecureChatConsumer.as_asgi()),
]
