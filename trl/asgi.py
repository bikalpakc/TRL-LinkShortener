import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import analytics.routing # We will create this in a second

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trl.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            analytics.routing.websocket_urlpatterns
        )
    ),
})