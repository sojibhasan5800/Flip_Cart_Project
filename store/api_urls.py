# store/api/urls.py
from django.urls import path
from .api_views import (
    ProductListCreateAPIView,
    ProductDetailAPIView,
    ReviewRatingListAPIView,
    ReviewRatingCreateAPIView,
    ProductGalleryListCreateAPIView,
    ProductGalleryDetailAPIView,
    VariationListCreateAPIView,
    VariationDetailAPIView,
    ProductSearchAPIView
)

app_name = 'store_api'

urlpatterns = [
    path('products/', ProductListCreateAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('reviews/', ReviewRatingListAPIView.as_view(), name='review-list'),
    path('reviews/create/', ReviewRatingCreateAPIView.as_view(), name='review-create'),
    path('galleries/', ProductGalleryListCreateAPIView.as_view(), name='gallery-list'),
    path('galleries/<int:pk>/', ProductGalleryDetailAPIView.as_view(), name='gallery-detail'),
    path('variations/', VariationListCreateAPIView.as_view(), name='variation-list'),
    path('variations/<int:pk>/', VariationDetailAPIView.as_view(), name='variation-detail'),
    path('search/', ProductSearchAPIView.as_view(), name='product-search'),
]
