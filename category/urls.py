from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'', views.CategoryViewSet,basename='categories_api_list')


urlpatterns = [
    path('load_Catagory/',views.load_category_object,name='category_load'),


    # ===================== Api Urls ===================================
    path('categories_api/',include(router.urls)),

]