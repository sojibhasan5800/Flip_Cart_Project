# accounts/api/urls.py
from django.urls import path
from .views import (
    RegistrationAPIView, LoginAPIView, LogoutAPIView, DashboardAPIView,
    EditProfileAPIView, ChangePasswordAPIView, MyOrdersAPIView, OrderDetailAPIView,
    ActivateAPIView, ForgotPasswordAPIView, ResetPasswordAPIView
)

app_name = "accounts_api"

urlpatterns = [
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('profile/', EditProfileAPIView.as_view(), name='profile'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
    path('my-orders/', MyOrdersAPIView.as_view(), name='my_orders'),
    path('order-detail/<int:order_id>/', OrderDetailAPIView.as_view(), name='order_detail'),
    path('activate/<uidb64>/<token>/', ActivateAPIView.as_view(), name='activate'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordAPIView.as_view(), name='reset_password'),
]
