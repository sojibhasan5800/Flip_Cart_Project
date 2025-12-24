from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone

class DeliveryOrganization(models.Model):
    """
    ডেলিভারি সার্ভিস প্রোভাইডার (Pathao, RedX, Paperfly, etc.)
    এটি একটি Shared Model (Tenant নয়)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True)
    
    # Company Information
    company_name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, blank=True)
    trade_license = models.CharField(max_length=100, blank=True)
    vat_registration = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    support_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    
    # Address
    head_office_address = models.TextField()
    branch_addresses = models.JSONField(default=list, blank=True)
    
    # Service Information
    service_areas = models.JSONField(
        default=list,
        help_text="List of districts/cities served (JSON array)"
    )
    
    service_types = models.JSONField(
        default=list,
        choices=[
            ('same_day', 'Same Day Delivery'),
            ('next_day', 'Next Day Delivery'),
            ('express', 'Express Delivery'),
            ('standard', 'Standard Delivery'),
            ('bulk', 'Bulk Delivery'),
            ('cod', 'Cash on Delivery'),
        ]
    )
    
    # Business Hours
    business_hours = models.JSONField(
        default=dict,
        help_text="Business hours in JSON format"
    )
    
    # API Integration
    has_api_integration = models.BooleanField(default=False)
    api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=500, blank=True)
    api_secret = models.CharField(max_length=500, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Rating & Reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Delivery Organization"
        verbose_name_plural = "Delivery Organizations"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.company_name})"
    
    @property
    def total_delivery_boys(self):
        return self.delivery_boys.count()
    
    @property
    def active_delivery_boys(self):
        return self.delivery_boys.filter(is_active=True).count()


class DeliveryBoy(models.Model):
    """
    ডেলিভারি বয়ের প্রোফাইল (Shared Model)
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_duty', 'On Duty'),
        ('off_duty', 'Off Duty'),
        ('on_leave', 'On Leave'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]
    
    VEHICLE_CHOICES = [
        ('bicycle', 'Bicycle'),
        ('motorcycle', 'Motorcycle'),
        ('scooter', 'Scooter'),
        ('car', 'Car'),
        ('van', 'Van'),
        ('pickup', 'Pickup Truck'),
        ('walking', 'Walking'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_organization = models.ForeignKey(
        DeliveryOrganization,
        on_delete=models.CASCADE,
        related_name='delivery_boys',
        null=True,
        blank=True
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_boy_profile'
    )
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], blank=True)
    
    # National ID & Documents
    nid_number = models.CharField(max_length=20, unique=True)
    nid_front_image = models.ImageField(upload_to='delivery_boy/nid/', blank=True, null=True)
    nid_back_image = models.ImageField(upload_to='delivery_boy/nid/', blank=True, null=True)
    
    # Contact Information
    phone = models.CharField(max_length=20, unique=True)
    alternative_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    
    # Address
    present_address = models.TextField()
    permanent_address = models.TextField()
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    
    # Vehicle Information
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, default='motorcycle')
    vehicle_brand = models.CharField(max_length=100, blank=True)
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_registration = models.CharField(max_length=100, blank=True)
    vehicle_color = models.CharField(max_length=50, blank=True)
    
    # License Information
    driving_license_number = models.CharField(max_length=100, blank=True)
    driving_license_image = models.ImageField(upload_to='delivery_boy/license/', blank=True, null=True)
    license_expiry_date = models.DateField(null=True, blank=True)
    
    # Employment Information
    employee_id = models.CharField(max_length=50, unique=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='contract')
    joining_date = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    
    # Salary & Commission
    salary_type = models.CharField(max_length=20, choices=[
        ('fixed', 'Fixed Salary'),
        ('commission', 'Commission Based'),
        ('hybrid', 'Fixed + Commission'),
        ('per_delivery', 'Per Delivery'),
    ], default='commission')
    
    fixed_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    per_delivery_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Bank Information
    bank_name = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    routing_number = models.CharField(max_length=50, blank=True)
    branch_name = models.CharField(max_length=100, blank=True)
    
    # Status & Availability
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    is_available = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Location Tracking
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Profile Photo
    profile_photo = models.ImageField(upload_to='delivery_boy/profile/', blank=True, null=True)
    
    # Documents
    profile_completion = models.IntegerField(default=0, help_text="Profile completion percentage")
    
    # Performance Metrics
    total_deliveries = models.PositiveIntegerField(default=0)
    successful_deliveries = models.PositiveIntegerField(default=0)
    failed_deliveries = models.PositiveIntegerField(default=0)
    cancelled_deliveries = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_rating_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Delivery Boy"
        verbose_name_plural = "Delivery Boys"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"
    
    @property
    def success_rate(self):
        if self.total_deliveries == 0:
            return 0
        return (self.successful_deliveries / self.total_deliveries) * 100
    
    @property
    def current_month_earnings(self):
        # This would be calculated from DeliveryTransaction model
        return 0
    
    @property
    def is_online(self):
        """Check if delivery boy is currently online"""
        if not self.last_active_at:
            return False
        import datetime
        time_diff = timezone.now() - self.last_active_at
        return time_diff < datetime.timedelta(minutes=5)
    
    def update_location(self, latitude, longitude):
        """Update delivery boy's current location"""
        self.current_latitude = latitude
        self.current_longitude = longitude
        self.last_location_update = timezone.now()
        self.save(update_fields=['current_latitude', 'current_longitude', 'last_location_update'])
    
    def mark_active(self):
        """Mark delivery boy as active and available"""
        self.status = 'on_duty'
        self.is_available = True
        self.last_active_at = timezone.now()
        self.save()
    
    def mark_inactive(self):
        """Mark delivery boy as inactive"""
        self.status = 'off_duty'
        self.is_available = False
        self.save()


class DeliveryBoyAttendance(models.Model):
    """ডেলিভারি বয়ের অ্যাটেন্ডেন্স রেকর্ড"""
    delivery_boy = models.ForeignKey(
        DeliveryBoy,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    
    date = models.DateField()
    check_in_time = models.DateTimeField()
    check_out_time = models.DateTimeField(null=True, blank=True)
    
    # Location
    check_in_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Work Summary
    total_deliveries = models.PositiveIntegerField(default=0)
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
    ], default='present')
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Delivery Boy Attendance"
        verbose_name_plural = "Delivery Boy Attendance Records"
        unique_together = ['delivery_boy', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.delivery_boy.full_name} - {self.date}"
    
    @property
    def working_hours(self):
        if not self.check_out_time:
            return 0
        delta = self.check_out_time - self.check_in_time
        return round(delta.total_seconds() / 3600, 2)


class DeliveryTransaction(models.Model):
    """ডেলিভারি বয়ের প্রতিটি ডেলিভারির লেনদেন"""
    delivery_boy = models.ForeignKey(
        DeliveryBoy,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    delivery_order = models.ForeignKey(
        'delivery_system.DeliveryOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    transaction_id = models.CharField(max_length=50, unique=True)
    transaction_type = models.CharField(max_length=20, choices=[
        ('delivery', 'Delivery Charge'),
        ('tip', 'Customer Tip'),
        ('bonus', 'Bonus'),
        ('penalty', 'Penalty'),
        ('adjustment', 'Adjustment'),
    ], default='delivery')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    
    # Commission Calculation
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Delivery Transaction"
        verbose_name_plural = "Delivery Transactions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.delivery_boy.full_name} - ৳{self.amount}"
    
    def calculate_commission(self):
        """Calculate commission for this transaction"""
        if self.transaction_type == 'delivery':
            self.commission_amount = (self.base_amount * self.commission_rate) / 100
            self.amount = self.commission_amount
        self.save()