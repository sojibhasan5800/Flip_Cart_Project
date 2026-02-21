
from django.urls import path,include
from . import views
# from rest_framework.routers import DefaultRouter
# router = DefaultRouter()
# router.register(r'', views.ProductViewSet,basename='product_api_list'),


urlpatterns = [
   path('', views.store, name='store'),

]