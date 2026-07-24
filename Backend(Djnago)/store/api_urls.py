# # store/api/urls.py
from django.urls import path
from .api_views import (
    ProductAPIView,
)

app_name = 'store_api'

urlpatterns = [
    
    path('products/', ProductAPIView.as_view(), name='product-list'),
]
