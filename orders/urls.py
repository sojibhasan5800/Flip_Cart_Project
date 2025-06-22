from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/<int:id>/<str:order_number>/<str:tk>/', views.payments, name='payments'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('order_complete/', views.order_complete, name='order_complete'),
]