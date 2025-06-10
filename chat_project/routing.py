from django.urls import path
from chat.consumers import TestConsumer

websocket_urlpatterns = [
    path("ws/test/", TestConsumer.as_asgi()),
]
