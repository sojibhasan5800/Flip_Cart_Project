# category/api/urls.py
from django.urls import path
from .api_views import (
    LoadCategoryAPIView,
    CategoryListAPIView,
    CategoryDetailAPIView
)

app_name = "category_api"

urlpatterns = [
    path('load/', LoadCategoryAPIView.as_view(), name='load_category'),
    path('', CategoryListAPIView.as_view(), name='list_create_category'),
    path('<int:pk>/', CategoryDetailAPIView.as_view(), name='detail_category'),
]
