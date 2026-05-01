# billing/routing.py
from django.urls import re_path
from .consumers import SubscriptionConsumer

websocket_urlpatterns = [
    re_path(r'ws/subscription/(?P<org_id>\d+)/$', SubscriptionConsumer.as_asgi()),
]