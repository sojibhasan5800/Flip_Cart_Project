# merchant_user/api_urls.py

from django.urls import path
from .api_views import (
   HomeProductsAPIView,
   LatestProductsAPIView
)

app_name = "public_data_api"

urlpatterns = [
    path('latest-products/', LatestProductsAPIView.as_view(), name='latest_products_api'),
    path('', HomeProductsAPIView.as_view(), name='home_products_api'),
]