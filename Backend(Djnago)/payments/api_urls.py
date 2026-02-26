from celery import app
from django.urls import path
from .api_views import CreatePaymentIntent, PaymentWebhook, RefundPayment, PurchasePlanView
from .webhooks import StripeWebhookView
app_name = 'payments_api'
urlpatterns = [
    path('create-intent/', CreatePaymentIntent.as_view(), name='create-payment-intent'),
    path('webhook/', PaymentWebhook.as_view(), name='payment-webhook'),
    path('refund/<int:trans_id>/', RefundPayment.as_view(), name='refund-payment'),
    path('plans/purchase-plan/', PurchasePlanView.as_view(), name='purchase-plan'),
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]