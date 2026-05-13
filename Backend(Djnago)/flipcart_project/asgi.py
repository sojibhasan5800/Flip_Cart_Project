import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import django
from merchant_user.routing import websocket_urlpatterns as merchant_websocket
from global_payments.routing import websocket_urlpatterns as payment_websocket

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flipcart_project.run_project.local')

django.setup()  # Ensure Django apps are loaded before importing routing

# from seller_dashboard import routing  # import after setup()
combined_websocket_urlpatterns = merchant_websocket + payment_websocket

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            combined_websocket_urlpatterns
        )
    ),
})
