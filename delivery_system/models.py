# delivery_system/models.py
from django.db import models
from django.conf import settings
from django_tenants.models import TenantMixin, DomainMixin
from orders.models import Order

class DeliveryTenant(TenantMixin):
    """
    Multi-tenant model for delivery system
    Each e-commerce store will have separate delivery settings
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Delivery Settings
    default_delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=60.00)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    auto_create_schema = True
    
    def __str__(self):
        return f"{self.name} (Tenant)"
    
    class Meta:
        verbose_name = "Delivery Tenant"
        verbose_name_plural = "Delivery Tenants"


class DeliveryDomain(DomainMixin):
    """
    Domain model for tenants
    """
    pass

class Division(models.Model):
    """Division Model - For the divisions of Bangladesh"""
    tenant = models.ForeignKey(DeliveryTenant, on_delete=models.CASCADE, related_name='divisions')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.tenant.name}"
    
    class Meta:
        verbose_name = "Division"
        
        verbose_name_plural = "Divisions"
        unique_together = ['tenant', 'name']

class District(models.Model):
    """District Model - Districts under each department"""
    tenant = models.ForeignKey(DeliveryTenant, on_delete=models.CASCADE, related_name='districts')
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.division.name} ({self.tenant.name})"
    
    class Meta:
        verbose_name = "District"
        verbose_name_plural = "Districts"
        unique_together = ['tenant', 'division', 'name']


class DeliveryArea(models.Model):
    """Delivery Area Model - District-wise Delivery Charges and Time"""
    tenant = models.ForeignKey(DeliveryTenant, on_delete=models.CASCADE, related_name='delivery_areas')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='delivery_areas')
    area_name = models.CharField(max_length=200)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    min_delivery_days = models.PositiveIntegerField(default=3)
    max_delivery_days = models.PositiveIntegerField(default=7)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.area_name}, {self.district.name} - ৳{self.delivery_charge} ({self.tenant.name})"
    
    class Meta:
        verbose_name = "Delivery Area"
        verbose_name_plural = "Delivery Areas"
        unique_together = ['tenant', 'district', 'area_name']


class DeliveryTimeSlot(models.Model):
    """ডেলিভারি টাইম স্লট - গ্রাহকরা তাদের পছন্দের সময় সিলেক্ট করতে পারবে"""
    TIME_SLOTS = [
        ('09:00-12:00', 'Morning (9:00 AM - 12:00 PM)'),
        ('12:00-15:00', 'Noon (12:00 PM - 3:00 PM)'),
        ('15:00-18:00', 'Afternoon (3:00 PM - 6:00 PM)'),
        ('18:00-21:00', 'Evening (6:00 PM - 9:00 PM)'),
    ]
    
    tenant = models.ForeignKey(DeliveryTenant, on_delete=models.CASCADE, related_name='time_slots')
    slot_name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_code = models.CharField(max_length=20, choices=TIME_SLOTS)
    is_available = models.BooleanField(default=True)
    max_orders_per_slot = models.PositiveIntegerField(default=50)
    current_orders = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.slot_name} ({self.start_time} - {self.end_time}) - {self.tenant.name}"
    
    class Meta:
        verbose_name = "Delivery Time Slot"
        verbose_name_plural = "Delivery Time Slots"
        unique_together = ['tenant', 'slot_code']