# billing/urls.py
from django.urls import path
from .api_views import (
    SubscriptionPlanListAPIView,
    OrganizationSubscriptionListCreateAPIView,
    subscription_upgrade_downgrade,
    subscription_invoices_list,
    ProductBoostSubscriptionListCreateAPIView,
)
app_name = 'billing_api'

urlpatterns = [
    path('plans/', SubscriptionPlanListAPIView.as_view(), name='plan-list'),
    
    path('subscriptions/', OrganizationSubscriptionListCreateAPIView.as_view(), name='subscription-list-create'),
    path('subscriptions/<int:subscription_id>/upgrade-downgrade/', subscription_upgrade_downgrade, name='subscription-upgrade-downgrade'),
    path('subscriptions/invoices/', subscription_invoices_list, name='subscription-invoices'),

    path('boosts/', ProductBoostSubscriptionListCreateAPIView.as_view(), name='boost-list-create'),
]