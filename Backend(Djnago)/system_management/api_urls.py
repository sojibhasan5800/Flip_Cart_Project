
from django.urls import path
from .api_views import (
    DashboardSchedulerControlAPIView,
)


app_name = 'system_management_api'

urlpatterns = [
    path('dashboard-scheduler/control/', DashboardSchedulerControlAPIView.as_view(), name='dashboard-scheduler-control'),
]
