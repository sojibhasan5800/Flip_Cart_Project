
from django.urls import path,include
from . import views
# from rest_framework.routers import DefaultRouter
# router = DefaultRouter()
# router.register(r'', views.ProductViewSet,basename='product_api_list'),


urlpatterns = [
   path('', views.store, name='store'),
   path('category/<slug:category_slug>/', views.store, name='products_by_category'),
   path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
   path('search/', views.search, name='search'),
   path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
   path('load_Product/',views.load_product_object,name='Product_load'),

   # ===================== Api Urls ===================================
   # path('product_api/',include(router.urls)),
   # path('review_list_api/',views.ReviewRatingListAPIView.as_view(),name='review_list_api'),
   # path('review_list_api/create/', views.ReviewRatingCreateAPIView.as_view(), name='review_list_api-create'),
]