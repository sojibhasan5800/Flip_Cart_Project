from django.urls import path
from .views import CreatePaymentIntent, PaymentWebhook, RefundPayment

urlpatterns = [
    path('create-intent/', CreatePaymentIntent.as_view(), name='create-payment-intent'),
    path('webhook/', PaymentWebhook.as_view(), name='payment-webhook'),
    path('refund/<int:trans_id>/', RefundPayment.as_view(), name='refund-payment'),
]