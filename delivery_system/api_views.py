# delivery_system/api_views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_tenants.utils import get_tenant, tenant_context

from orders.models import Order 

from .models import (
    Division, District, DeliveryArea, DeliveryTimeSlot, 
    DeliveryOrder, DeliveryTracking, DeliverySettings
)
from .serializers import (
    DivisionSerializer, DistrictSerializer, DeliveryAreaSerializer,
    DeliveryTimeSlotSerializer, DeliveryOrderSerializer, DeliveryTrackingSerializer,
    DeliveryCalculatorSerializer, DeliverySettingsSerializer
)
# from orders.models import Order


class DivisionListAPIView(generics.ListAPIView):
    """
    get:
    Return list of all active divisions for current tenant.
    """
    serializer_class = DivisionSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        tenant = get_tenant()
        return Division.objects.filter(tenant=tenant, is_active=True).order_by('name')
    
    @swagger_auto_schema(
        operation_summary="Get all active divisions for current tenant",
        operation_description="Retrieve list of all active divisions for the current tenant's delivery service.",
        tags=['Delivery']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DistrictListByDivisionAPIView(generics.ListAPIView):
    """
    get:
    Return list of districts by division ID for current tenant.
    """
    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        tenant = get_tenant()
        division_id = self.kwargs['division_id']
        return District.objects.filter(
            division_id=division_id, 
            tenant=tenant,
            is_active=True
        ).order_by('name')
    
    @swagger_auto_schema(
        operation_summary="Get districts by division for current tenant",
        operation_description="Retrieve list of all active districts under a specific division for current tenant.",
        tags=['Delivery']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DeliveryAreaListByDistrictAPIView(generics.ListAPIView):
    """
    get:
    Return list of delivery areas by district ID for current tenant.
    """
    serializer_class = DeliveryAreaSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        tenant = get_tenant()
        district_id = self.kwargs['district_id']
        return DeliveryArea.objects.filter(
            district_id=district_id, 
            tenant=tenant,
            is_available=True
        ).order_by('area_name')
    
    @swagger_auto_schema(
        operation_summary="Get delivery areas by district for current tenant",
        operation_description="Retrieve list of all available delivery areas under a specific district for current tenant.",
        tags=['Delivery']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DeliveryTimeSlotListAPIView(generics.ListAPIView):
    """
    get:
    Return list of available delivery time slots for current tenant.
    """
    serializer_class = DeliveryTimeSlotSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        tenant = get_tenant()
        return DeliveryTimeSlot.objects.filter(
            tenant=tenant, 
            is_available=True
        ).order_by('start_time')
    
    @swagger_auto_schema(
        operation_summary="Get available delivery time slots for current tenant",
        operation_description="Retrieve list of all available delivery time slots for order placement for current tenant.",
        tags=['Delivery']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CalculateDeliveryChargeAPIView(APIView):
    """
    post:
    Calculate delivery charge for a given location for current tenant.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Calculate delivery charge for current tenant",
        operation_description="Calculate delivery charge and estimated delivery time for a given location for current tenant.",
        request_body=DeliveryCalculatorSerializer,
        responses={
            200: openapi.Response(
                description="Delivery calculation successful",
                examples={
                    "application/json": {
                        "status": True,
                        "delivery_charge": 60.00,
                        "min_delivery_days": 3,
                        "max_delivery_days": 5,
                        "estimated_delivery_date": "2024-01-15",
                        "message": "Delivery charge calculated successfully"
                    }
                }
            )
        },
        tags=['Delivery']
    )
    def post(self, request):
        serializer = DeliveryCalculatorSerializer(data=request.data)
        
        if serializer.is_valid():
            delivery_area = serializer.validated_data['delivery_area']
            tenant = serializer.validated_data['tenant']
            order_total = serializer.validated_data.get('order_total', 0)
            
            # Calculate delivery charge based on tenant settings
            delivery_charge = delivery_area.delivery_charge
            
            # Apply free delivery if order total exceeds threshold
            if order_total >= tenant.free_delivery_threshold:
                delivery_charge = 0.00
            
            # Calculate estimated delivery date
            from datetime import datetime, timedelta
            today = datetime.now().date()
            min_delivery_date = today + timedelta(days=delivery_area.min_delivery_days)
            max_delivery_date = today + timedelta(days=delivery_area.max_delivery_days)
            
            response_data = {
                "status": True,
                "tenant": tenant.name,
                "delivery_charge": float(delivery_charge),
                "min_delivery_days": delivery_area.min_delivery_days,
                "max_delivery_days": delivery_area.max_delivery_days,
                "estimated_delivery_date": min_delivery_date.isoformat(),
                "delivery_area_id": delivery_area.id,
                "free_delivery_available": order_total >= tenant.free_delivery_threshold,
                "free_delivery_threshold": float(tenant.free_delivery_threshold),
                "message": "Delivery charge calculated successfully"
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response({
            "status": False,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DeliveryOrderCreateAPIView(APIView):
    """
    post:
    Create delivery order when payment is completed for current tenant.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Create delivery order for current tenant",
        operation_description="Create a new delivery order after successful payment processing for current tenant.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_id', 'delivery_area_id'],
            properties={
                'order_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Order ID'),
                'delivery_area_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Delivery Area ID'),
                'delivery_time_slot_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Delivery Time Slot ID (optional)'),
            }
        ),
        responses={
            201: openapi.Response(
                description="Delivery order created successfully"
            )
        },
        tags=['Delivery Orders']
    )
    def post(self, request):
        order_id = request.data.get('order_id')
        delivery_area_id = request.data.get('delivery_area_id')
        delivery_time_slot_id = request.data.get('delivery_time_slot_id')
        tenant = get_tenant()
        
        try:
            with transaction.atomic():
                # Get order and validate
                # order = get_object_or_404(Order, id=order_id, user=request.user)
                order = get_object_or_404(Order, id=order_id, user=request.user)
                delivery_area = get_object_or_404(
                    DeliveryArea, 
                    id=delivery_area_id, 
                    tenant=tenant,
                    is_available=True
                )
                
                # Check if delivery order already exists
                if hasattr(order, 'delivery_order'):
                    return Response({
                        "status": False,
                        "message": "Delivery order already exists for this order"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get time slot if provided
                delivery_time_slot = None
                if delivery_time_slot_id:
                    delivery_time_slot = get_object_or_404(
                        DeliveryTimeSlot, 
                        id=delivery_time_slot_id, 
                        tenant=tenant,
                        is_available=True
                    )
                    # Update current orders count
                    delivery_time_slot.current_orders += 1
                    delivery_time_slot.save()
                
                # Calculate delivery charge
                delivery_charge = delivery_area.delivery_charge
                if order.order_total >= tenant.free_delivery_threshold:
                    delivery_charge = 0.00
                
                # Calculate estimated delivery date
                from datetime import datetime, timedelta
                today = datetime.now().date()
                estimated_delivery_date = today + timedelta(days=delivery_area.min_delivery_days)
                
                # Create delivery order
                delivery_order = DeliveryOrder.objects.create(
                    tenant=tenant,
                    order=order,
                    delivery_area=delivery_area,
                    delivery_charge=delivery_charge,
                    delivery_time_slot=delivery_time_slot,
                    estimated_delivery_date=estimated_delivery_date,
                    status='confirmed'
                )
                
                # Create initial tracking record
                DeliveryTracking.objects.create(
                    tenant=tenant,
                    delivery_order=delivery_order,
                    status='confirmed',
                    description="Delivery order confirmed and ready for processing"
                )
                
                # Send notification based on tenant settings
                self.send_delivery_confirmation_notification(delivery_order)
                
                return Response({
                    "status": True,
                    "tenant": tenant.name,
                    "delivery_id": delivery_order.delivery_id,
                    "message": "Delivery order created successfully",
                    "estimated_delivery_date": estimated_delivery_date.isoformat(),
                    "delivery_charge": float(delivery_charge)
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error creating delivery order: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def send_delivery_confirmation_notification(self, delivery_order):
        """Send delivery confirmation notification based on tenant settings"""
        try:
            settings = DeliverySettings.objects.get(tenant=delivery_order.tenant)
            if settings.send_delivery_notifications and settings.notify_on_creation:
                # Implement notification logic here
                print(f"Notification sent for delivery {delivery_order.delivery_id}")
        except DeliverySettings.DoesNotExist:
            pass


class DeliveryOrderDetailAPIView(generics.RetrieveAPIView):
    """
    get:
    Retrieve delivery order details and tracking information for current tenant.
    """
    serializer_class = DeliveryOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'delivery_id'
    lookup_url_kwarg = 'delivery_id'
    
    def get_queryset(self):
        tenant = get_tenant()
        return DeliveryOrder.objects.filter(
            tenant=tenant,
            order__user=self.request.user
        )
    
    @swagger_auto_schema(
        operation_summary="Get delivery order details for current tenant",
        operation_description="Retrieve detailed information about a specific delivery order for current tenant.",
        tags=['Delivery Orders']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DeliveryOrderListAPIView(generics.ListAPIView):
    """
    get:
    List all delivery orders for authenticated user in current tenant.
    """
    serializer_class = DeliveryOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant = get_tenant()
        return DeliveryOrder.objects.filter(
            tenant=tenant,
            order__user=self.request.user
        ).order_by('-created_at')
    
    @swagger_auto_schema(
        operation_summary="List user delivery orders for current tenant",
        operation_description="Retrieve paginated list of all delivery orders for authenticated user in current tenant.",
        tags=['Delivery Orders']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class DeliverySettingsAPIView(APIView):
    """
    get:
    Retrieve delivery settings for current tenant.
    
    put:
    Update delivery settings for current tenant (Admin only).
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method == 'PUT':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @swagger_auto_schema(
        operation_summary="Get delivery settings for current tenant",
        responses={200: DeliverySettingsSerializer},
        tags=['Delivery Settings']
    )
    def get(self, request):
        tenant = get_tenant()
        settings, created = DeliverySettings.objects.get_or_create(tenant=tenant)
        serializer = DeliverySettingsSerializer(settings)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Update delivery settings for current tenant",
        request_body=DeliverySettingsSerializer,
        responses={200: DeliverySettingsSerializer},
        tags=['Delivery Settings']
    )
    def put(self, request):
        tenant = get_tenant()
        settings = get_object_or_404(DeliverySettings, tenant=tenant)
        serializer = DeliverySettingsSerializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateDeliveryStatusAPIView(APIView):
    """
    post:
    Update delivery order status for current tenant (Admin only).
    """
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Update delivery status for current tenant",
        operation_description="Update delivery order status and create tracking history for current tenant (Admin only).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['delivery_id', 'status'],
            properties={
                'delivery_id': openapi.Schema(type=openapi.TYPE_STRING, description='Delivery Order ID'),
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='New status',
                    enum=['picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'cancelled']
                ),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Status description'),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description='Current location'),
            }
        ),
        tags=['Delivery Management']
    )
    def post(self, request):
        delivery_id = request.data.get('delivery_id')
        new_status = request.data.get('status')
        description = request.data.get('description', '')
        location = request.data.get('location', '')
        tenant = get_tenant()
        
        try:
            delivery_order = get_object_or_404(
                DeliveryOrder, 
                delivery_id=delivery_id,
                tenant=tenant
            )
            
            with transaction.atomic():
                # Update delivery order status
                delivery_order.status = new_status
                if new_status == 'delivered':
                    delivery_order.actual_delivery_date = timezone.now().date()
                delivery_order.save()
                
                # Create tracking history
                DeliveryTracking.objects.create(
                    tenant=tenant,
                    delivery_order=delivery_order,
                    status=new_status,
                    description=description or self.get_default_status_description(new_status),
                    location=location
                )
                
                # Send status update notification
                self.send_status_update_notification(delivery_order, new_status)
                
                return Response({
                    "status": True,
                    "tenant": tenant.name,
                    "message": f"Delivery status updated to {new_status}",
                    "delivery_id": delivery_id
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Error updating delivery status: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def get_default_status_description(self, status):
        """Get default description for status updates"""
        descriptions = {
            'picked_up': 'Package has been picked up from warehouse',
            'in_transit': 'Package is in transit to delivery hub',
            'out_for_delivery': 'Package is out for delivery',
            'delivered': 'Package has been delivered successfully',
            'cancelled': 'Delivery has been cancelled'
        }
        return descriptions.get(status, 'Status updated')
    
    def send_status_update_notification(self, delivery_order, new_status):
        """Send status update notification based on tenant settings"""
        try:
            settings = DeliverySettings.objects.get(tenant=delivery_order.tenant)
            if settings.send_delivery_notifications and settings.notify_on_status_change:
                # Implement notification logic here
                print(f"Status update notification sent for delivery {delivery_order.delivery_id}")
        except DeliverySettings.DoesNotExist:
            pass