# merchant_user/api_urls.py

from django.urls import path
from .api_views import (
    MerchantStoreCreateAPIView,SellerStatusAPIView,SellerStoreDashboardAPIView,MerchantProductAPIView, ToggleStockAPIView
)

app_name = "merchant_user_api"

urlpatterns = [
    path('merchant/store/create/', MerchantStoreCreateAPIView.as_view(), name='merchant_store_create'),
    
    path('seller-status/', SellerStatusAPIView.as_view(), name='seller_status'),
    path('seller-store-dashboard/', SellerStoreDashboardAPIView.as_view(), name='seller_store_dashboard'),
    path('merchant-products/',  MerchantProductAPIView.as_view(),  name="merchant-products"),
    path('products/toggle-stock/<int:pk>/', ToggleStockAPIView.as_view(), name='toggle-stock'),
]