# merchant_user/api_urls.py

from django.urls import path
from .api_views import (
   HomeProductsAPIView,
   LatestProductsAPIView,
   ProductDetailView,
   ProductReviewsView,
)

app_name = "public_data_api"

urlpatterns = [
    path('latest-products/', LatestProductsAPIView.as_view(), name='latest_products_api'),
    path('all-shop-products/', HomeProductsAPIView.as_view(), name='all_shop_products_api'),
    path('product/<int:product_id>/', ProductDetailView.as_view(), name='product_detail_api'),
    path('product/<int:product_id>/reviews/', ProductReviewsView.as_view(), name='product_reviews_api'),
]