# merchant_user/api_urls.py

from django.urls import path
from .api_views import (
   HomeProductsAPIView
)

app_name = "public_data_api"

urlpatterns = [
    path('', HomeProductsAPIView.as_view(), name='home_products_api'),
]