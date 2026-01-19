from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Organization, OrganizationDomain, MerchantUser


# ===============================
# Organization Admin
# ===============================
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "business_name",
        "username",
        "schema_name",
        "subscription_plan",
        "subscription_status",
        "is_trial",
        "is_active",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "subscription_plan",
        "subscription_status",
        "is_trial",
        "is_active",
        "is_verified",
        "business_type",
        "country",
    )

    search_fields = (
        "business_name",
        "username",
        "business_email",
        "phone",
        "schema_name",
    )

    readonly_fields = (
        "id",
        "schema_name",
        "created_at",
        "updated_at",
        "days_remaining_in_trial_display",
        "store_url_display",
    )

    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "id",
                "username",
                "business_name",
                "store_logo",
                "schema_name",
                "duplicate_schema_name",
            )
        }),
        ("Business Contact", {
            "fields": (
                "business_email",
                "phone",
                "website",
                "store_description",
            )
        }),
        ("Address", {
            "fields": (
                "address_line1",
                "address_line2",
                "city",
                "state",
                "postal_code",
                "country",
            )
        }),
        ("Subscription & Billing", {
            "fields": (
                "subscription_plan",
                "subscription_status",
                "stripe_customer_id",
                "stripe_subscription_id",
                "current_period_start",
                "current_period_end",
                "is_trial",
                "trial_ends_at",
                "days_remaining_in_trial_display",
            )
        }),
        ("Limits & Features", {
            "fields": (
                "max_users",
                "max_products",
                "max_storage_gb",
                "max_monthly_orders",
            )
        }),
        ("Delivery", {
            "fields": ("delivery_integration",)
        }),
        ("Status", {
            "fields": (
                "is_active",
                "is_verified",
                "is_suspended",
            )
        }),
        ("Audit", {
            "fields": (
                "created_at",
                "updated_at",
                "onboarded_at",
                "store_url_display",
            )
        }),
    )

    @admin.display(description="Trial Days Left")
    def days_remaining_in_trial_display(self, obj):
        return obj.days_remaining_in_trial

    @admin.display(description="Store URL")
    def store_url_display(self, obj):
        if obj.store_url:
            return format_html(
                '<a href="{0}" target="_blank">{0}</a>',
                obj.store_url
            )
        return "-"


# ===============================
# Organization Domain Admin
# ===============================
@admin.register(OrganizationDomain)
class OrganizationDomainAdmin(admin.ModelAdmin):
    list_display = (
        "domain",
        "tenant",
        "domain_type",
        "is_primary",
        "ssl_status",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "domain_type",
        "ssl_status",
        "is_verified",
        "created_at",
    )

    search_fields = (
        "domain",
        "tenant__business_name",
        "tenant__schema_name",
    )

    raw_id_fields = ("tenant",)
    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "updated_at",
        "verified_at",
    )

    fieldsets = (
        ("Domain Mapping", {
            "fields": (
                "tenant",
                "domain",
                "domain_type",
                "is_primary",
            )
        }),
        ("SSL Configuration", {
            "fields": (
                "ssl_status",
                "ssl_certificate",
                "ssl_private_key",
                "ssl_expiry_date",
            )
        }),
        ("Verification", {
            "fields": (
                "is_verified",
                "verification_token",
                "verified_at",
            )
        }),
        ("DNS Records", {
            "fields": (
                "a_record",
                "cname_record",
                "txt_record",
            )
        }),
        ("Analytics", {
            "fields": (
                "google_site_verification",
            )
        }),
        ("Audit", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


# ===============================
# Merchant User Admin
# ===============================
@admin.register(MerchantUser)
class MerchantUserAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "organization",
        "role",
        "department",
        "is_active",
        "can_login_admin",
        "last_login_at",
        "joined_at",
    )

    list_filter = (
        "role",
        "is_active",
        "can_login_admin",
        "two_factor_enabled",
        "joined_at",
    )

    search_fields = (
        "user__email",
        "organization__business_name",
        "department",
        "designation",
        "employee_id",
    )

    raw_id_fields = ("organization", "user")
    ordering = ("-joined_at",)

    readonly_fields = (
        "joined_at",
        "updated_at",
        "last_login_at",
        "last_activity_at",
    )

    fieldsets = (
        ("User Mapping", {
            "fields": (
                "organization",
                "user",
                "role",
            )
        }),
        ("Job Information", {
            "fields": (
                "department",
                "designation",
                "employee_id",
            )
        }),
        ("Permissions", {
            "fields": (
                "permissions",
                "can_login_admin",
            )
        }),
        ("Contact", {
            "fields": (
                "work_email",
                "work_phone",
                "emergency_contact",
            )
        }),
        ("Security", {
            "fields": (
                "two_factor_enabled",
                "last_password_change",
            )
        }),
        ("Status & Activity", {
            "fields": (
                "is_active",
                "is_verified",
                "last_login_at",
                "last_activity_at",
            )
        }),
        ("Audit", {
            "fields": (
                "joined_at",
                "updated_at",
            )
        }),
    )
