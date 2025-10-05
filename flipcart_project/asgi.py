import os
import django
from channels.routing import get_default_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flipcart_project.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import seller_dashboard.routing  # Point

application = ProtocolTypeRouter({
    "http": get_default_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            seller_dashboard.routing.websocket_urlpatterns
        )
    ),
})
