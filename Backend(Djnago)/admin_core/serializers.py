# serializers.py
from rest_framework import serializers
from django.utils import timezone
import re

from merchant_user.models import MerchantUser, Organization
from accounts.models import Account, UserProfile
from .models import Coupon


class SimpleUserSerializer(serializers.ModelSerializer):
    """
    Minimal user information — used when showing owner/creator in nested responses
    """
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'full_name',
            'profile_picture',
        ]

    def get_full_name(self, obj):
        """Returns the full name using the model's full_name() method"""
        return obj.full_name()

    def get_profile_picture(self, obj):
        """Returns Cloudinary profile picture URL or None"""
        try:
            return obj.userprofile.profile_picture.url
        except UserProfile.DoesNotExist:
            return None


class OrganizationApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer used mainly in admin/approval views to show organization + owner details
    """
    user = serializers.SerializerMethodField(
        help_text="The merchant user who owns this organization (role='owner')"
    )

    class Meta:
        model = Organization
        fields = [
            'id',
            'business_name',
            'username',
            'store_description',
            'store_logo',
            'business_email',
            'phone',
            'address_line1',
            'is_verified',
            'is_active',
            # 'rejection_reason',    # uncomment when needed
            'created_at',
            'user',
        ]
        read_only_fields = ['created_at']

    def get_user(self, obj):
        """Returns basic info of the organization owner (if exists)"""
        merchant_user = MerchantUser.objects.filter(
            organization=obj,
            role='owner'
        ).first()

        if merchant_user:
            return SimpleUserSerializer(merchant_user.user).data
        return None


# admin_core/serializers.py
class CouponSerializer(serializers.ModelSerializer):
    """
    Main serializer for Coupon model — used in both admin and merchant APIs

    Important notes:
    • Merchants can only create coupons for their own organization
    • Superadmins can create coupons for any organization (via organization field)
    • Automatic status & days_until_expiry are calculated
    """
    status = serializers.CharField(read_only=True,
        help_text="Current status of the coupon (auto-calculated)")
    
    days_until_expiry = serializers.SerializerMethodField(
        help_text="Days remaining until coupon expires (0 if already expired)"
    )

    class Meta:
        model = Coupon
        fields = [
            'id',
            'code',
            'description',
            'discount',
            'is_active',
            'is_expired',
            'for_new_user',
            'for_member',
            'is_public',
            'status',
            'valid_from',
            'valid_to',
            'created_at',
            'usage_limit',
            'used_count',
            'min_order_value',
            'celery_task_id',
            'days_until_expiry',
            'organization',          # important: visible in API + writable by superadmin
        ]
        read_only_fields = [
            'id',
            'created_at',
            # 'updated_at',         # add if you have updated_at field
            'used_count',
            'is_expired',
            'status',
            'celery_task_id',
        ]

    def get_days_until_expiry(self, obj):
        """Calculate remaining days until valid_to date"""
        if obj.valid_to:
            delta = obj.valid_to - timezone.now()
            return max(0, delta.days)
        return None

    def validate_code(self, value):
        """Coupon code must contain only uppercase letters and numbers"""
        if not re.match(r'^[A-Z0-9]+$', value):
            raise serializers.ValidationError(
                "Coupon code can only contain uppercase letters and numbers."
            )
        return value.upper()

    def validate_discount(self, value):
        """Discount percentage must be between 1 and 100"""
        if value <= 0 or value > 100:
            raise serializers.ValidationError(
                "Discount must be between 1 and 100."
            )
        return value

    def validate(self, data):
        """
        Cross-field validation:
        - valid_to must be in future
        - valid_to must be after valid_from
        """
        # For update → use existing values if not provided
        valid_to   = data.get('valid_to',   getattr(self.instance, 'valid_to',   None))
        valid_from = data.get('valid_from', getattr(self.instance, 'valid_from', timezone.now()))

        if valid_to and valid_to <= timezone.now():
            raise serializers.ValidationError({
                "valid_to": "Expiry date must be in the future."
            })

        if valid_to and valid_from and valid_to <= valid_from:
            raise serializers.ValidationError({
                "valid_to": "Expiry date must be after start date."
            })

        return data

    def create(self, validated_data):
        """
        Custom create logic:
        • Normal merchants → automatically assign their own organization
        • Superadmins   → organization comes from request body
        """
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is missing.")

        user = request.user

        # For merchant users: force their own organization
        if not user.is_superadmin:
            if not hasattr(user, 'organization') or not user.organization:
                raise serializers.ValidationError(
                    "This user is not associated with any store/organization."
                )
            validated_data['organization'] = user.organization

        # For superadmin: organization should come from request data
        # (you can make it required in swagger / via extra validation if needed)

        coupon = Coupon.objects.create(**validated_data)
        return coupon