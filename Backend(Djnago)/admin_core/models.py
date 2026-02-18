# models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
from datetime import  timedelta

class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    for_new_user = models.BooleanField(default=False)
    for_member = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    # Timing fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    
    # Advanced fields
    usage_limit = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Task tracking for Celery
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Tenant relation
    organization = models.ForeignKey(
        'merchant_user.Organization', 
        on_delete=models.SET_NULL,
        related_name='coupons',
        null = True, blank=True
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['code', 'organization']),
            models.Index(fields=['valid_to', 'is_active']),
            models.Index(fields=['is_expired', 'is_active']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} (Expires: {self.valid_to.strftime('%Y-%m-%d %H:%M')})"
    
    def clean(self):
        if self.valid_to <= self.valid_from:
            raise ValidationError("Expiry date must be after start date.")
        if self.valid_to <= timezone.now():
            raise ValidationError("Expiry date must be in the future.")
    
    @property
    def status(self):
        now = timezone.now()
        if self.is_expired:
            return "expired"
        elif not self.is_active:
            return "inactive"
        elif now > self.valid_to:
            return "expired"
        elif now < self.valid_from:
            return "upcoming"
        else:
            return "active"
    
    def schedule_expiry_task(self):
        """Schedule a one-time task for coupon expiry"""
        from .tasks import expire_single_coupon_task
        
        # Calculate delay in seconds
        now = timezone.now()
        delay_seconds = max(0, (self.valid_to - now).total_seconds())
        
        # Schedule task
        task = expire_single_coupon_task.apply_async(
            args=[str(self.id)], 
            eta=self.valid_to,
            expires=self.valid_to + timedelta(minutes=5)  # 5 minutes grace period
        )
        
        # IMPORTANT: update() ব্যবহার করছি যাতে post_save signal আবার ফায়ার না হয়
        Coupon.objects.filter(id=self.id).update(celery_task_id=task.id)
        # self.save(update_fields=['celery_task_id'])
        return task.id
    
    def cancel_scheduled_task(self):
        """Cancel the scheduled expiry task"""
        if self.celery_task_id:
            from celery.result import AsyncResult
            from flipcart_project.celery import app
            
            try:
                app.control.revoke(self.celery_task_id, terminate=True)
                # update() দিয়ে celery_task_id ক্লিয়ার করা
                Coupon.objects.filter(id=self.id).update(celery_task_id=None)
                # self.save(update_fields=['celery_task_id'])

            except Exception as e:
                # Task might have already executed
                pass

