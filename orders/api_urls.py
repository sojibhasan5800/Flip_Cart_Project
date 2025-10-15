# orders/api/urls.py
from django.urls import path
from .api_views import OrderListCreateAPIView, OrderDetailAPIView, PaymentSuccessAPIView

app_name = "orders_api"

urlpatterns = [
    path('', OrderListCreateAPIView.as_view(), name='list_create_order'),
    path('<int:pk>/', OrderDetailAPIView.as_view(), name='detail_order'),
    path('payment-success/', PaymentSuccessAPIView.as_view(), name='payment_success_api'),
]
