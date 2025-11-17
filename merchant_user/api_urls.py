# accounts/api/urls.py
from django.urls import path
from .api_views import (
    MerchantRegistrationAPIView, MerchantDashboardAPIView,
    MerchantSubscriptionAPIView, ReactivateSubscriptionAPIView,SubscriptionPlansAPIView
)

app_name = "merchant_user_api"

urlpatterns = [
    # Versioned merchant APIs
    path('merchant/register/', MerchantRegistrationAPIView.as_view(), name='merchant_register'),
    path('merchant/dashboard/', MerchantDashboardAPIView.as_view(), name='merchant_dashboard'),
    path('merchant/subscription/', MerchantSubscriptionAPIView.as_view(), name='merchant_subscription'),
    path('merchant/subscription/reactivate/', ReactivateSubscriptionAPIView.as_view(), name='merchant_subscription_reactivate'),
    path('subscription/plans/', SubscriptionPlansAPIView.as_view(), name='subscription_plans'),
]
