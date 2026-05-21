
from django.urls import path
from .api_views import ShippingAddressAPIView


app_name = 'orders_management_api'

urlpatterns = [
    path('shipping-addresses/', ShippingAddressAPIView.as_view(), name='shipping-addresses'),
]