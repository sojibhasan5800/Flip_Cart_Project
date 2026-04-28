# billing/urls.py
from django.urls import path
from .api_views import (

    AdminInvoiceDetailAPIView,
    AdminInvoiceListAPIView,
    AdminOrganizationSubscriptionDetailAPIView,
    AdminOrganizationSubscriptionListAPIView,
    AdminProductBoostDetailAPIView,
    AdminProductBoostListAPIView,
    AdminSubscriptionPlanDetailAPIView,
    AdminSubscriptionPlanListCreateAPIView,
    PublicOrganizationPlanListAPIView,
    PlusMembershipPlanListAPIView,
    ProductBoostSubscriptionListAPIView,  
    CurrentSubscriptionAPIView,
    UpgradeSubscriptionAPIView,
    DowngradeAtPeriodEndAPIView,
    CancelSubscriptionAPIView,
    SubscriptionProrationAPIView,



    # SubscriptionPlanListAPIView,
    # OrganizationSubscriptionListCreateAPIView,
    # subscription_upgrade_downgrade,
    # subscription_invoices_list,
    # ProductBoostSubscriptionListCreateAPIView,
)
app_name = 'billing_api'

urlpatterns = [


    # --------------------- Admin endpoints ---------------------
    path("plans/", AdminSubscriptionPlanListCreateAPIView.as_view()),
    path("plans/<int:pk>/", AdminSubscriptionPlanDetailAPIView.as_view()),

    path("org-subscriptions/", AdminOrganizationSubscriptionListAPIView.as_view()),
    path("org-subscriptions/<int:pk>/", AdminOrganizationSubscriptionDetailAPIView.as_view()),

    path("boosts/", AdminProductBoostListAPIView.as_view()),
    path("boosts/<int:pk>/", AdminProductBoostDetailAPIView.as_view()),

    path("invoices/", AdminInvoiceListAPIView.as_view()),
    path("invoices/<int:pk>/", AdminInvoiceDetailAPIView.as_view()),

    # --------------------- Public endpoints ---------------------
    path("org-plans/", PublicOrganizationPlanListAPIView.as_view()),
    
    path("plus-membership/", PlusMembershipPlanListAPIView.as_view()),
    path("product-boosts/", ProductBoostSubscriptionListAPIView.as_view()),
    path('current-subscription/', CurrentSubscriptionAPIView.as_view(),name='current-subscription'),
    path('upgrade-subscription/', UpgradeSubscriptionAPIView.as_view(),name='upgrade-subscription'),
    path('downgrade-at-period-end/', DowngradeAtPeriodEndAPIView.as_view(),name='downgrade-at-period-end'),
    path('cancel-subscription/', CancelSubscriptionAPIView.as_view(),name='cancel-subscription'),
    path('subscription-proration/', SubscriptionProrationAPIView.as_view(), name='subscription-proration'),
    # path('plans/', SubscriptionPlanListAPIView.as_view(), name='plan-list'),
    
    # path('subscriptions/', OrganizationSubscriptionListCreateAPIView.as_view(), name='subscription-list-create'),
    # path('subscriptions/<int:subscription_id>/upgrade-downgrade/', subscription_upgrade_downgrade, name='subscription-upgrade-downgrade'),
    # path('subscriptions/invoices/', subscription_invoices_list, name='subscription-invoices'),

    # path('boosts/', ProductBoostSubscriptionListCreateAPIView.as_view(), name='boost-list-create'),
]