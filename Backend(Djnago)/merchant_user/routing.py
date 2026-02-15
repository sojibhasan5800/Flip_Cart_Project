from django.urls import re_path
from .consumers import MerchantDashboardConsumer

websocket_urlpatterns = [
    re_path(r'ws/dashboard/(?P<org_id>\d+)/$', MerchantDashboardConsumer.as_asgi()),
]