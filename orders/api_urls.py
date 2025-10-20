from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'orders_api'

router = DefaultRouter()
router.register('orders', api_views.OrderViewSet, basename='orders')
router.register('payments', api_views.PaymentViewSet, basename='payments')
router.register('order-products', api_views.OrderProductViewSet, basename='order-products')

urlpatterns = [
    path('', include(router.urls)),
    path('stripe/webhook/', api_views.StripeWebhookAPIView.as_view(), name='stripe-webhook'),
    path('stripe/success/', api_views.StripeSuccessAPIView.as_view(), name='stripe-success'),
    path('stripe/cancel/', api_views.StripeCancelAPIView.as_view(), name='stripe-cancel'),
]
