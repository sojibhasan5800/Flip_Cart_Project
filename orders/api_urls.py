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
    path('place-order/', api_views.PlaceOrderAPIView.as_view(), name='place-order'),
    path('stripe/create-session/', api_views.CreateStripeSessionAPIView.as_view(), name='stripe-create-session'),
    path('stripe/webhook/', api_views.StripeWebhookAPIView.as_view(), name='stripe-webhook'),
    path('stripe/success/', api_views.StripeSuccessAPIView.as_view(), name='stripe-success'),
    path('stripe/cancel/', api_views.StripeCancelAPIView.as_view(), name='stripe-cancel'),

    path('ssl-payment/', api_views.SSLPaymentAPIView.as_view(), name='ssl_payment'),
    path('ssl/success/', api_views.PaymentSuccessAPIView.as_view(), name='payment_success'),
    path('ssl/fail/', api_views.PaymentFailAPIView.as_view(), name='payment_fail'),
    path('ssl/cancel/', api_views.PaymentCancelAPIView.as_view(), name='payment_cancel'),

]
