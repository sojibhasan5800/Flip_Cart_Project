from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='seller_dashboard'),
    path('ajax/', views.dashboard_ajax, name='seller_dashboard_ajax'),
]