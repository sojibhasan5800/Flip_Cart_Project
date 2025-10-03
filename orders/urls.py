from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments_ssl/<int:id>/<str:order_number>/<str:tk>/', views.payments_ssl, name='payments_ssl'),
    path('payments_stripe/<int:id>/<str:order_number>/<str:tk>/', views.payments_stripe, name='payments_stripe'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('order_complete/', views.order_complete, name='order_complete'),
]