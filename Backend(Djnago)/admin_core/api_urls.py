# urls.py (coupon app)
from django.urls import path
from .api_views import (
    CouponListCreateAPIView,
    CouponDetailAPIView,
    CouponStatsAPIView,
    CouponToggleAPIView,
    PublicAdminCheckAPIView,
    SuperAdminDashboardAPIView,
    AdminStoreApprovalAPIView,
    ToggleScheduleAPIView,
    DashboardSchedulerControlAPIView
)

# Application namespace – used in reverse() calls: reverse('admin_core_api:coupon-list-create')
app_name = 'admin_core_api'

urlpatterns = [
    # ───────────────────────────────────────────────
    #              Public / Common endpoints
    # ───────────────────────────────────────────────
    # Anyone can call this to check if they have admin rights
    path('check/', PublicAdminCheckAPIView.as_view(), name='admin-check'),

    # ───────────────────────────────────────────────
    #              Super Admin endpoints
    # ───────────────────────────────────────────────
    path('dashboard/super-admin/', SuperAdminDashboardAPIView.as_view(), name='super-admin-dashboard'),

    # ───────────────────────────────────────────────
    #              Admin / Store Management
    # ───────────────────────────────────────────────
    path('store-approval/', AdminStoreApprovalAPIView.as_view(), name='store-approval'),

    # ───────────────────────────────────────────────
    #              Coupon Management Endpoints
    # ───────────────────────────────────────────────
    # GET    → list all coupons + statistics overview
    # POST   → create new coupon
    path('coupons/', CouponListCreateAPIView.as_view(), name='coupon-list-create'),

    # GET    → get detailed info of one coupon
    path('coupons/<str:code>/', CouponDetailAPIView.as_view(), name='coupon-detail'),

    # POST   → activate / deactivate / delete coupon
    # Example: /coupons/SUMMER2025/activate/
    #         /coupons/BLACKFRIDAY/deactivate/
    path('coupons/<str:code>/<str:action>/', CouponToggleAPIView.as_view(), name='coupon-toggle'),

    # GET    → coupon usage statistics (most used, expired, etc.)
    # Previously fixed URL – kept for backward compatibility / frontend
    path('coupons/stats/', CouponStatsAPIView.as_view(), name='coupon-stats'),
    path("schedule/toggle/", ToggleScheduleAPIView.as_view()),
    path('dashboard-scheduler/control/', DashboardSchedulerControlAPIView.as_view(), name='dashboard-scheduler-control'),
]