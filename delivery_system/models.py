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
    auto_drop_schema = True
    
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


class DeliveryOrder(models.Model):
    """Delivery Order Model - Automatically created when payment is complete"""
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Delivery Failed'),
    ]
    
    # Tenant Information
    tenant = models.ForeignKey(DeliveryTenant, on_delete=models.CASCADE, related_name='delivery_orders')
    
    # Order Information
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery_order')
    delivery_id = models.CharField(max_length=20, unique=True, blank=True)
    
    # Delivery Information
    delivery_area = models.ForeignKey(DeliveryArea, on_delete=models.SET_NULL, null=True)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_time_slot = models.ForeignKey(DeliveryTimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='pending')
    status_changed_at = models.DateTimeField(auto_now=True)
    
    # Delivery Agent Information
    delivery_agent_name = models.CharField(max_length=100, blank=True)
    delivery_agent_phone = models.CharField(max_length=15, blank=True)
    
    # Tracking Information
    tracking_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Delivery #{self.delivery_id} for Order #{self.order.order_number} ({self.tenant.name})"
    
    def save(self, *args, **kwargs):
        if not self.delivery_id:
            self.delivery_id = self.generate_delivery_id()
        super().save(*args, **kwargs)
    
    def generate_delivery_id(self):
        """Generate unique delivery ID"""
        import uuid
        return f"DL{self.tenant.name[:2].upper()}{uuid.uuid4().hex[:6].upper()}"
    
    class Meta:
        verbose_name = "Delivery Order"
        verbose_name_plural = "Delivery Orders"
        ordering = ['-created_at']






class DeliveryTracking(models.Model):
    """ডেলিভারি ট্র্যাকিং মডেল - প্রতিটি স্ট্যাটাস চেঞ্জের হিস্ট্রি রাখবে"""
    tenant = models.ForeignKey(DeliveryTenant, on_delete=models.CASCADE, related_name='tracking_history')
    delivery_order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=20, choices=DeliveryOrder.DELIVERY_STATUS)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.delivery_order.delivery_id} - {self.status} at {self.created_at} ({self.tenant.name})"
    
    class Meta:
        verbose_name = "Delivery Tracking"
        verbose_name_plural = "Delivery Tracking History"
        ordering = ['-created_at']


class DeliverySettings(models.Model):
    """Tenant-based delivery settings"""
    tenant = models.OneToOneField(DeliveryTenant, on_delete=models.CASCADE, related_name='settings')
    
    # General Settings
    auto_create_delivery = models.BooleanField(default=True, 
        help_text="Automatically create delivery order when payment is completed")
    send_delivery_notifications = models.BooleanField(default=True,
        help_text="Send SMS/Email notifications for delivery updates")
    
    # Delivery Rules
    same_day_delivery = models.BooleanField(default=False)
    same_day_cutoff_time = models.TimeField(default='14:00', 
        help_text="Order before this time for same day delivery")
    
    # Notification Settings
    notify_on_creation = models.BooleanField(default=True)
    notify_on_status_change = models.BooleanField(default=True)
    notify_on_delivery = models.BooleanField(default=True)
    
    # Integration Settings
    sms_gateway_enabled = models.BooleanField(default=False)
    email_notifications_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Delivery Settings - {self.tenant.name}"
    
    class Meta:
        verbose_name = "Delivery Settings"
        verbose_name_plural = "Delivery Settings"




#----------------------new ----------------------------
