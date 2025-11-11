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