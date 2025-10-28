# accounts/api/urls.py
from django.urls import path
from .api_views import (
    RegistrationAPIView, LoginAPIView, LogoutAPIView, DashboardAPIView,
    EditProfileAPIView, ChangePasswordAPIView, MyOrdersAPIView, OrderDetailAPIView,
    ActivateAPIView, ForgotPasswordAPIView, ResetPasswordAPIView,ResetPasswordValidateAPIView,DeleteAccountAPIView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
    path('reset-password-validate/<uidb64>/<token>/', ResetPasswordValidateAPIView.as_view(), name='api_reset_password_validate'),
    path('reset-password/', ResetPasswordAPIView.as_view(), name='reset_password'),
    path('delete-account/', DeleteAccountAPIView.as_view(), name='delete_account'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),      # login JWT
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),     # refresh JWT
]
