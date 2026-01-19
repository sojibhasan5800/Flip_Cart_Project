# admin.py
from django.contrib import admin
from django.utils import timezone
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'organization', 'valid_to', 
                   'status_display', 'is_active', 'used_count')
    list_filter = ('is_active', 'is_expired', 'for_new_user', 
                  'for_member', 'organization', 'valid_to')
    search_fields = ('code', 'description')
    readonly_fields = ('created_at', 'updated_at', 'celery_task_id', 'status_display')
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description', 'discount', 'organization')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to', 'is_active')
        }),
        ('Rules', {
            'fields': ('for_new_user', 'for_member', 'is_public',
                      'usage_limit', 'used_count', 'min_order_value')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'celery_task_id', 
                      'status_display', 'is_expired')
        }),
    )
    
    actions = ['deactivate_selected', 'activate_selected', 'schedule_expiry_tasks']
    
    def status_display(self, obj):
        now = timezone.now()
        if obj.is_expired or obj.valid_to < now:
            return "Expired"
        elif not obj.is_active:
            return "Inactive"
        elif obj.valid_from > now:
            return "Upcoming"
        else:
            return "Active"
    status_display.short_description = "Status"
    
    def deactivate_selected(self, request, queryset):
        for coupon in queryset:
            coupon.is_active = False
            coupon.cancel_scheduled_task()
            coupon.save()
        self.message_user(request, f"{queryset.count()} coupons deactivated.")
    deactivate_selected.short_description = "Deactivate selected coupons"
    
    def activate_selected(self, request, queryset):
        activated = 0
        for coupon in queryset:
            if coupon.valid_to > timezone.now():
                coupon.is_active = True
                coupon.schedule_expiry_task()
                coupon.save()
                activated += 1
        self.message_user(request, f"{activated} coupons activated.")
    activate_selected.short_description = "Activate selected coupons"
    
    def schedule_expiry_tasks(self, request, queryset):
        scheduled = 0
        for coupon in queryset:
            if coupon.is_active and coupon.valid_to > timezone.now():
                coupon.schedule_expiry_task()
                scheduled += 1
        self.message_user(request, f"Scheduled expiry tasks for {scheduled} coupons.")
    schedule_expiry_tasks.short_description = "Schedule expiry tasks"