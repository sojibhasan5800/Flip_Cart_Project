# delivery_system/serializers.py
from rest_framework import serializers
from django_tenants.utils import tenant_context
from .models import (
    DeliveryTenant, Division, District, DeliveryArea, 
    DeliveryTimeSlot, DeliveryOrder, DeliveryTracking, DeliverySettings
)


class DeliveryTenantSerializer(serializers.ModelSerializer):
    """Serializer for Delivery Tenant model"""
    
    class Meta:
        model = DeliveryTenant
        fields = [
            'id', 'name', 'description', 'default_delivery_charge', 
            'free_delivery_threshold', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DivisionSerializer(serializers.ModelSerializer):
    """Serializer for Division model"""
    
    class Meta:
        model = Division
        fields = ['id', 'name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class DistrictSerializer(serializers.ModelSerializer):
    """Serializer for District model"""
    division_name = serializers.CharField(source='division.name', read_only=True)
    
    class Meta:
        model = District
        fields = ['id', 'name', 'division', 'division_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class DeliveryAreaSerializer(serializers.ModelSerializer):
    """Serializer for Delivery Area model"""
    district_name = serializers.CharField(source='district.name', read_only=True)
    division_name = serializers.CharField(source='district.division.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = DeliveryArea
        fields = [
            'id', 'tenant', 'tenant_name', 'district', 'district_name', 'division_name', 
            'area_name', 'delivery_charge', 'min_delivery_days', 'max_delivery_days',
            'is_available', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DeliveryTimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for Delivery Time Slot model"""
    is_available_today = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = DeliveryTimeSlot
        fields = [
            'id', 'tenant', 'tenant_name', 'slot_name', 'start_time', 'end_time', 
            'slot_code', 'is_available', 'max_orders_per_slot', 'current_orders',
            'is_available_today'
        ]
        read_only_fields = ['id', 'current_orders']
    
    def get_is_available_today(self, obj):
        """Check if time slot is available for today"""
        from datetime import datetime
        today = datetime.now().date()
        return obj.current_orders < obj.max_orders_per_slot


class DeliveryTrackingSerializer(serializers.ModelSerializer):
    """Serializer for Delivery Tracking history"""
    
    class Meta:
        model = DeliveryTracking
        fields = ['id', 'status', 'description', 'location', 'created_at']
        read_only_fields = ['id', 'created_at']


class DeliveryOrderSerializer(serializers.ModelSerializer):
    """Serializer for Delivery Order model"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    customer_name = serializers.CharField(source='order.full_name', read_only=True)
    customer_phone = serializers.CharField(source='order.phone', read_only=True)
    customer_address = serializers.CharField(source='order.full_address', read_only=True)
    delivery_area_details = DeliveryAreaSerializer(source='delivery_area', read_only=True)
    time_slot_details = DeliveryTimeSlotSerializer(source='delivery_time_slot', read_only=True)
    tracking_history = DeliveryTrackingSerializer(many=True, read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = DeliveryOrder
        fields = [
            'id', 'tenant', 'tenant_name', 'delivery_id', 'order', 'order_number', 
            'customer_name', 'customer_phone', 'customer_address', 
            'delivery_area', 'delivery_area_details', 'delivery_charge', 
            'delivery_time_slot', 'time_slot_details', 'estimated_delivery_date', 
            'actual_delivery_date', 'status', 'delivery_agent_name', 
            'delivery_agent_phone', 'tracking_url', 'notes', 'tracking_history', 
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tenant', 'delivery_id', 'created_at', 'updated_at', 'tracking_history'
        ]


class DeliverySettingsSerializer(serializers.ModelSerializer):
    """Serializer for Delivery Settings"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = DeliverySettings
        fields = [
            'id', 'tenant', 'tenant_name', 'auto_create_delivery', 
            'send_delivery_notifications', 'same_day_delivery', 
            'same_day_cutoff_time', 'notify_on_creation', 
            'notify_on_status_change', 'notify_on_delivery',
            'sms_gateway_enabled', 'email_notifications_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at']


class DeliveryCalculatorSerializer(serializers.Serializer):
    """Serializer for delivery charge calculation"""
    district_id = serializers.IntegerField(required=True)
    area_name = serializers.CharField(required=True)
    order_total = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    def validate(self, data):
        """Validate district and area for current tenant"""
        from django_tenants.utils import get_tenant
        from .models import District, DeliveryArea
        
        tenant = get_tenant()
        
        try:
            district = District.objects.get(
                id=data['district_id'], 
                tenant=tenant,
                is_active=True
            )
            delivery_area = DeliveryArea.objects.get(
                district=district,
                area_name=data['area_name'],
                tenant=tenant,
                is_available=True
            )
            data['delivery_area'] = delivery_area
            data['tenant'] = tenant
        except District.DoesNotExist:
            raise serializers.ValidationError({"district_id": "Invalid district ID for this tenant"})
        except DeliveryArea.DoesNotExist:
            raise serializers.ValidationError({"area_name": "Delivery not available in this area for this tenant"})
        
        return data