from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    # ws://localhost:8000/ws/analytics/
    path('ws/analytics/', consumers.AnalyticsConsumer.as_asgi()),
]