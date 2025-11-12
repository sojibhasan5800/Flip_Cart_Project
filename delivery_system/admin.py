# # delivery_system/admin.py
# from django.contrib import admin
# from django_tenants.admin import TenantAdminMixin
# from .models import (
#     DeliveryTenant, DeliveryDomain, Division, District, 
#     DeliveryArea, DeliveryTimeSlot, DeliveryOrder, 
#     DeliveryTracking, DeliverySettings
# )


# @admin.register(DeliveryTenant)
# class DeliveryTenantAdmin(TenantAdminMixin, admin.ModelAdmin):
#     list_display = [
#         'name', 'schema_name', 'default_delivery_charge', 
#         'free_delivery_threshold', 'is_active', 'created_at'
#     ]
#     list_filter = ['is_active', 'created_at']
#     search_fields = ['name', 'description']
#     list_editable = ['default_delivery_charge', 'free_delivery_threshold', 'is_active']


# @admin.register(DeliveryDomain)
# class DeliveryDomainAdmin(admin.ModelAdmin):
#     list_display = ['domain', 'tenant', 'is_primary']
#     list_filter = ['is_primary']
#     search_fields = ['domain', 'tenant__name']


# class DistrictInline(admin.TabularInline):
#     model = District
#     extra = 0
#     show_change_link = True


# @admin.register(Division)
# class DivisionAdmin(admin.ModelAdmin):
#     list_display = ['name', 'tenant', 'is_active', 'created_at']
#     list_filter = ['tenant', 'is_active']
#     search_fields = ['name', 'tenant__name']
#     list_editable = ['is_active']
#     inlines = [DistrictInline]


# class DeliveryAreaInline(admin.TabularInline):
#     model = DeliveryArea
#     extra = 0
#     show_change_link = True


# @admin.register(District)
# class DistrictAdmin(admin.ModelAdmin):
#     list_display = ['name', 'division', 'tenant', 'is_active', 'created_at']
#     list_filter = ['division__tenant', 'division', 'is_active']
#     search_fields = ['name', 'division__name']
#     list_editable = ['is_active']
#     inlines = [DeliveryAreaInline]


# @admin.register(DeliveryArea)
# class DeliveryAreaAdmin(admin.ModelAdmin):
#     list_display = [
#         'area_name', 'district', 'tenant', 'delivery_charge', 
#         'min_delivery_days', 'max_delivery_days', 'is_available'
#     ]
#     list_filter = ['district__division__tenant', 'district__division', 'district', 'is_available']
#     search_fields = ['area_name', 'district__name']
#     list_editable = ['delivery_charge', 'min_delivery_days', 'max_delivery_days', 'is_available']


# @admin.register(DeliveryTimeSlot)
# class DeliveryTimeSlotAdmin(admin.ModelAdmin):
#     list_display = [
#         'slot_name', 'tenant', 'start_time', 'end_time', 
#         'slot_code', 'is_available', 'current_orders', 'max_orders_per_slot'
#     ]
#     list_filter = ['tenant', 'is_available']
#     list_editable = ['is_available', 'max_orders_per_slot']


# class DeliveryTrackingInline(admin.TabularInline):
#     model = DeliveryTracking
#     extra = 0
#     readonly_fields = ['created_at']
#     can_delete = False


# @admin.register(DeliveryOrder)
# class DeliveryOrderAdmin(admin.ModelAdmin):
#     list_display = [
#         'delivery_id', 'order', 'tenant', 'status', 'delivery_charge', 
#         'estimated_delivery_date', 'created_at'
#     ]
#     list_filter = ['tenant', 'status', 'delivery_area__district', 'created_at']
#     search_fields = ['delivery_id', 'order__order_number', 'order__user__email']
#     readonly_fields = ['delivery_id', 'created_at', 'updated_at']
#     inlines = [DeliveryTrackingInline]
#     list_editable = ['status']
    
#     fieldsets = (
#         ('Tenant Information', {
#             'fields': ('tenant',)
#         }),
#         ('Order Information', {
#             'fields': ('order', 'delivery_id')
#         }),
#         ('Delivery Information', {
#             'fields': ('delivery_area', 'delivery_charge', 'delivery_time_slot', 'estimated_delivery_date', 'actual_delivery_date')
#         }),
#         ('Status Information', {
#             'fields': ('status', 'delivery_agent_name', 'delivery_agent_phone', 'tracking_url', 'notes')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )


# @admin.register(DeliveryTracking)
# class DeliveryTrackingAdmin(admin.ModelAdmin):
#     list_display = ['delivery_order', 'tenant', 'status', 'location', 'created_at']
#     list_filter = ['tenant', 'status', 'created_at']
#     search_fields = ['delivery_order__delivery_id', 'delivery_order__order__order_number']
#     readonly_fields = ['created_at']
    
#     def has_add_permission(self, request):
#         return False


# @admin.register(DeliverySettings)
# class DeliverySettingsAdmin(admin.ModelAdmin):
#     list_display = [
#         'tenant', 'auto_create_delivery', 'send_delivery_notifications',
#         'same_day_delivery', 'updated_at'
#     ]
#     list_filter = ['tenant', 'auto_create_delivery', 'send_delivery_notifications']
#     search_fields = ['tenant__name']
    
#     fieldsets = (
#         ('Tenant', {
#             'fields': ('tenant',)
#         }),
#         ('General Settings', {
#             'fields': ('auto_create_delivery', 'send_delivery_notifications')
#         }),
#         ('Delivery Rules', {
#             'fields': ('same_day_delivery', 'same_day_cutoff_time')
#         }),
#         ('Notification Settings', {
#             'fields': ('notify_on_creation', 'notify_on_status_change', 'notify_on_delivery')
#         }),
#         ('Integration Settings', {
#             'fields': ('sms_gateway_enabled', 'email_notifications_enabled')
#         }),
#     )