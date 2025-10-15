"""
URL configuration for flipcart_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="FlipCart API",
      default_version='v1',
      description="API docs for FlipCart project (accounts module shown)",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('home_api_load_products/', views.home, name='home_api_load_products'),
    path('store/', include('store.urls')),
    path('carts/', include('carts.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('category/', include('category.urls')),
    path('seller_dashboard/', include('seller_dashboard.urls')),

    # # path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # api path ------------

    path('api/accounts/', include('accounts.api_urls', namespace='accounts_api')),
    path('api/category/', include('category.api_urls', namespace='category_api')),
    path('api/carts/', include('carts.api_urls', namespace='carts_api')),
    path('api/store/', include('store.api.urls', namespace='store_api')),
    path('api/orders/', include('orders.urls', namespace='orders_api'))



    path('swagger(<format>.json|.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
