# # # delivery_system/api_urls.py
# app_name = 'delivery_system_api'

# from django.urls import path
# from .api_views import (
#     DivisionListAPIView,
#     DistrictListByDivisionAPIView,
#     DeliveryAreaListByDistrictAPIView,
#     DeliveryTimeSlotListAPIView,
#     CalculateDeliveryChargeAPIView,
#     DeliveryOrderCreateAPIView,
#     DeliveryOrderDetailAPIView,
#     DeliveryOrderListAPIView,
#     DeliverySettingsAPIView,
#     UpdateDeliveryStatusAPIView
# )



# urlpatterns = [
#     # Location APIs
#     path('divisions/', DivisionListAPIView.as_view(), name='division-list'),
#     path('divisions/<int:division_id>/districts/', DistrictListByDivisionAPIView.as_view(), name='district-list'),
#     path('districts/<int:district_id>/areas/', DeliveryAreaListByDistrictAPIView.as_view(), name='area-list'),
#     path('time-slots/', DeliveryTimeSlotListAPIView.as_view(), name='time-slot-list'),
    
#     # Delivery Calculation API
#     path('calculate-charge/', CalculateDeliveryChargeAPIView.as_view(), name='calculate-charge'),
    
#     # Delivery Order APIs
#     path('orders/create/', DeliveryOrderCreateAPIView.as_view(), name='create-delivery-order'),
#     path('orders/', DeliveryOrderListAPIView.as_view(), name='delivery-order-list'),
#     path('orders/<str:delivery_id>/', DeliveryOrderDetailAPIView.as_view(), name='delivery-order-detail'),
    
#     # Delivery Settings API
#     path('settings/', DeliverySettingsAPIView.as_view(), name='delivery-settings'),
    
#     # Admin APIs
#     path('admin/update-status/', UpdateDeliveryStatusAPIView.as_view(), name='update-delivery-status'),
# ]