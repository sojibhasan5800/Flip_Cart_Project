from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone

# REMOVE DeliveryTenant model completely
# DeliverySystem will be a tenant-specific app

class Division(models.Model):
    """বিভাগ (ঢাকা, চট্টগ্রাম, etc.)"""
    tenant = models.ForeignKey(
        'merchant_user.Organization',  # Tenant model
        on_delete=models.CASCADE,
        related_name='divisions'
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Division"
        verbose_name_plural = "Divisions"
        unique_together = ['tenant', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class District(models.Model):
    """জেলা"""
    tenant = models.ForeignKey(
        'merchant_user.Organization',
        on_delete=models.CASCADE,
        related_name='districts'
    )
    
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "District"
        verbose_name_plural = "Districts"
        unique_together = ['tenant', 'division', 'name']
    
    def __str__(self):
        return f"{self.name}, {self.division.name} ({self.tenant.name})"


class DeliveryZone(models.Model):
    """ডেলিভারি জোন (এলাকা ভিত্তিক চার্জ)"""
    tenant = models.ForeignKey(
        'merchant_user.Organization',
        on_delete=models.CASCADE,
        related_name='delivery_zones'
    )
    
    name = models.CharField(max_length=200)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='delivery_zones')
    areas = models.JSONField(
        default=list,
        help_text="List of areas in this zone (JSON array)"
    )
    
    # Delivery Charges
    standard_charge = models.DecimalField(max_digits=10, decimal_places=2, default=60.00)
    express_charge = models.DecimalField(max_digits=10, decimal_places=2, default=120.00)
    same_day_charge = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    
    # Delivery Time
    standard_delivery_days = models.PositiveIntegerField(default=3)
    express_delivery_days = models.PositiveIntegerField(default=1)
    same_day_delivery_hours = models.PositiveIntegerField(default=6)
    
    # Free Delivery
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Delivery Zone"
        verbose_name_plural = "Delivery Zones"
        unique_together = ['tenant', 'district', 'name']
    
    def __str__(self):
        return f"{self.name}, {self.district.name} - ৳{self.standard_charge}"


class DeliveryTimeSlot(models.Model):
    """ডেলিভারি টাইম স্লট"""
    TIME_SLOTS = [
        ('09:00-12:00', 'Morning (9:00 AM - 12:00 PM)'),
        ('12:00-15:00', 'Noon (12:00 PM - 3:00 PM)'),
        ('15:00-18:00', 'Afternoon (3:00 PM - 6:00 PM)'),
        ('18:00-21:00', 'Evening (6:00 PM - 9:00 PM)'),
    ]
    
    DAYS_OF_WEEK = [
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]
    
    tenant = models.ForeignKey(
        'merchant_user.Organization',
        on_delete=models.CASCADE,
        related_name='delivery_time_slots'
    )
    
    slot_name = models.CharField(max_length=100)
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_code = models.CharField(max_length=20, choices=TIME_SLOTS)
    
    # Capacity
    max_orders = models.PositiveIntegerField(default=50)
    current_orders = models.PositiveIntegerField(default=0)
    
    # Status
    is_available = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Delivery Time Slot"
        verbose_name_plural = "Delivery Time Slots"
        unique_together = ['tenant', 'day_of_week', 'slot_code']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} - {self.slot_name} ({self.start_time} - {self.end_time})"
    
    @property
    def available_slots(self):
        return self.max_orders - self.current_orders
    
    def can_accept_order(self):
        return self.is_available and self.current_orders < self.max_orders


class DeliveryOrder(models.Model):
    """ডেলিভারি অর্ডার (Tenant-specific)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Delivery Failed'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    DELIVERY_TYPE_CHOICES = [
        ('standard', 'Standard Delivery'),
        ('express', 'Express Delivery'),
        ('same_day', 'Same Day Delivery'),
        ('scheduled', 'Scheduled Delivery'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'merchant_user.Organization',
        on_delete=models.CASCADE,
        related_name='delivery_orders'
    )
    
    # Order Reference
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery_order'
    )
    
    # Delivery Information
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE_CHOICES, default='standard')
    delivery_zone = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_time_slot = models.ForeignKey(DeliveryTimeSlot, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Charges
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    additional_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Dates
    estimated_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    delivery_start_time = models.DateTimeField(null=True, blank=True)
    delivery_end_time = models.DateTimeField(null=True, blank=True)
    
    # Delivery Agent
    assigned_delivery_boy = models.ForeignKey(
        'delivery_user.DeliveryBoy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_deliveries'
    )
    
    assigned_delivery_organization = models.ForeignKey(
        'delivery_user.DeliveryOrganization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders'
    )
    
    # Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, unique=True, blank=True)
    tracking_url = models.URLField(blank=True)
    
    # Delivery Address
    recipient_name = models.CharField(max_length=200)
    recipient_phone = models.CharField(max_length=20)
    delivery_address = models.TextField()
    delivery_instructions = models.TextField(blank=True)
    
    # Payment
    is_cod = models.BooleanField(default=False)
    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ], default='pending')
    
    # Notes
    internal_notes = models.TextField(blank=True)
    customer_notes = models.TextField(blank=True)
    
    # Ratings
    delivery_rating = models.PositiveIntegerField(null=True, blank=True)
    delivery_feedback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_changed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Delivery Order"
        verbose_name_plural = "Delivery Orders"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_number']),
            models.Index(fields=['status']),
            models.Index(fields=['estimated_delivery_date']),
        ]
    
    def __str__(self):
        return f"Delivery #{self.tracking_number or self.id} for Order #{self.order.order_number}"
    
    def save(self, *args, **kwargs):
        # Generate tracking number
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        
        # Calculate total charge
        self.total_charge = self.delivery_charge + self.additional_charges
        
        super().save(*args, **kwargs)
    
    def generate_tracking_number(self):
        """Generate unique tracking number"""
        import time
        prefix = self.tenant.name[:3].upper()
        timestamp = str(int(time.time()))[-8:]
        random_part = uuid.uuid4().hex[:6].upper()
        return f"{prefix}{timestamp}{random_part}"
    
    @property
    def delivery_time_taken(self):
        """Calculate delivery time taken"""
        if self.delivery_start_time and self.delivery_end_time:
            delta = self.delivery_end_time - self.delivery_start_time
            hours = delta.total_seconds() / 3600
            return round(hours, 2)
        return None
    
    def assign_delivery_boy(self, delivery_boy):
        """Assign delivery boy to this order"""
        self.assigned_delivery_boy = delivery_boy
        self.status = 'confirmed'
        self.save()
        
        # Create tracking history
        DeliveryTracking.objects.create(
            delivery_order=self,
            status='confirmed',
            description=f"Delivery assigned to {delivery_boy.full_name}",
            location=self.delivery_address
        )
    
    def update_status(self, new_status, description=""):
        """Update delivery status with tracking history"""
        old_status = self.status
        self.status = new_status
        self.status_changed_at = timezone.now()
        self.save()
        
        # Create tracking record
        DeliveryTracking.objects.create(
            delivery_order=self,
            status=new_status,
            description=description or f"Status changed from {old_status} to {new_status}",
            location=self.delivery_address
        )
        
        # If delivered, update actual delivery date
        if new_status == 'delivered':
            self.actual_delivery_date = timezone.now().date()
            self.delivery_end_time = timezone.now()
            self.save()
            
            # Update delivery boy's stats
            if self.assigned_delivery_boy:
                self.assigned_delivery_boy.total_deliveries += 1
                self.assigned_delivery_boy.successful_deliveries += 1
                self.assigned_delivery_boy.save()


class DeliveryTracking(models.Model):
    """ডেলিভারি ট্র্যাকিং হিস্ট্রি"""
    delivery_order = models.ForeignKey(
        DeliveryOrder,
        on_delete=models.CASCADE,
        related_name='tracking_history'
    )
    
    status = models.CharField(max_length=20, choices=DeliveryOrder.STATUS_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    
    # Agent information (if applicable)
    handled_by = models.CharField(max_length=200, blank=True)
    handled_by_type = models.CharField(max_length=20, choices=[
        ('system', 'System'),
        ('merchant', 'Merchant'),
        ('delivery_boy', 'Delivery Boy'),
        ('customer', 'Customer'),
    ], default='system')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Delivery Tracking"
        verbose_name_plural = "Delivery Tracking History"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.delivery_order.tracking_number} - {self.status} at {self.created_at}"


class DeliverySettings(models.Model):
    """প্রতিটি Tenant-এর ডেলিভারি সেটিংস"""
    tenant = models.OneToOneField(
        'merchant_user.Organization',
        on_delete=models.CASCADE,
        related_name='delivery_settings'
    )
    
    # General Settings
    auto_create_delivery = models.BooleanField(
        default=True,
        help_text="Automatically create delivery order when order is paid"
    )
    
    # Delivery Options
    enable_standard_delivery = models.BooleanField(default=True)
    enable_express_delivery = models.BooleanField(default=True)
    enable_same_day_delivery = models.BooleanField(default=False)
    enable_scheduled_delivery = models.BooleanField(default=False)
    
    # Charges
    default_delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=60.00)
    express_delivery_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=60.00)
    same_day_delivery_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=140.00)
    
    # Free Delivery
    enable_free_delivery = models.BooleanField(default=True)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    
    # Cash on Delivery
    enable_cod = models.BooleanField(default=True)
    cod_charge = models.DecimalField(max_digits=10, decimal_places=2, default=20.00)
    max_cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    
    # Delivery Time
    standard_delivery_time = models.PositiveIntegerField(default=3, help_text="Days")
    express_delivery_time = models.PositiveIntegerField(default=1, help_text="Days")
    same_day_cutoff_time = models.TimeField(default='14:00')
    
    # Notifications
    notify_on_delivery_creation = models.BooleanField(default=True)
    notify_on_status_change = models.BooleanField(default=True)
    notify_on_delivery = models.BooleanField(default=True)
    notify_customer = models.BooleanField(default=True)
    
    # Integration
    external_delivery_enabled = models.BooleanField(default=False)
    default_delivery_organization = models.ForeignKey(
        'delivery_user.DeliveryOrganization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Advanced Settings
    require_delivery_confirmation = models.BooleanField(default=False)
    allow_delivery_time_selection = models.BooleanField(default=True)
    allow_delivery_instructions = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Delivery Settings"
        verbose_name_plural = "Delivery Settings"
    
    def __str__(self):
        return f"Delivery Settings - {self.tenant.name}"
    
    def get_delivery_charge(self, cart_total, delivery_type='standard'):
        """Calculate delivery charge based on cart total and delivery type"""
        if self.enable_free_delivery and cart_total >= self.free_delivery_threshold:
            return 0.00
        
        if delivery_type == 'standard':
            return self.default_delivery_charge
        elif delivery_type == 'express':
            return self.default_delivery_charge + self.express_delivery_surcharge
        elif delivery_type == 'same_day':
            return self.default_delivery_charge + self.same_day_delivery_surcharge
        else:
            return self.default_delivery_charge