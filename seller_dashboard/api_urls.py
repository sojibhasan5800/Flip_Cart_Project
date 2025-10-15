# seller_dashboard/api/urls.py
from django.urls import path
from .api_views import SellerAnalyticsAPIView

app_name = 'seller_dashboard_api'

urlpatterns = [
    path('analytics/', SellerAnalyticsAPIView.as_view(), name='analytics'),
]
