# # home/urls.py
# from django.urls import path
# from . import views
# from .api_views import HomeProductsAPIView, LoadMoreProductsAPIView

# urlpatterns = [
#     # path('', views.home, name='home'),
    
#     # API URLs
#     path('', HomeProductsAPIView.as_view(), name='home_products_api'),
#     path('api/load-more-products/', LoadMoreProductsAPIView.as_view(), name='load_more_products_api'),
# ]