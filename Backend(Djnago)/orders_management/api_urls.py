
from django.urls import path
from .api_views import ShippingAddressCreateAPIView


app_name = 'orders_management_api'

urlpatterns = [
    path('shipping-addresses/', ShippingAddressCreateAPIView.as_view(), name='shipping-addresses'),
]