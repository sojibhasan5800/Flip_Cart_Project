from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Account, UserProfile, Tenant
from accounts.serializers import RegistrationSerializer, AccountSerializer,UserProfileSerializer
import re


class MerchantRegistrationSerializer(serializers.Serializer):
    """Serializer for merchant registration with business details"""
    
    # Business information
    business_name = serializers.CharField(max_length=100, write_only=True)
    subdomain = serializers.CharField(max_length=50, write_only=True)
    
    # Personal information
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate_subdomain(self, value):
        """Validate subdomain format and availability"""
        value = value.lower().strip()
        
        # Check format (alphanumeric and hyphens only)
        if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', value):
            raise serializers.ValidationError(
                'Subdomain can only contain lowercase letters, numbers, and hyphens. Cannot start or end with hyphen.'
            )
        
        # Check reserved subdomains
        reserved = ['www', 'admin', 'api', 'blog', 'support', 'help', 'mail', 'ftp', 'cpanel', 'webmail']
        if value in reserved:
            raise serializers.ValidationError('This subdomain is reserved. Please choose another one.')
        
        # Check length
        if len(value) < 3:
            raise serializers.ValidationError('Subdomain must be at least 3 characters long.')
        if len(value) > 50:
            raise serializers.ValidationError('Subdomain cannot exceed 50 characters.')
        
        # Check availability
        if Tenant.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError('This subdomain is already taken. Please choose another one.')
        
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value
    
    def validate_password(self, value):
        """Validate password strength"""
        validate_password(value)
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data

class MerchantUserRegistrationSerializer(RegistrationSerializer):
    """
    Merchant registration serializer
    Only adds tenant to user creation, no duplication of logic
    """
    def create(self, validated_data):
        # get tenant from context
        tenant = self.context.get("tenant")
        
        # save user using the parent serializer's create logic
        # temporarily store tenant, then assign it after user creation
        user = super().create(validated_data)  # call parent RegistrationSerializer.create()

        # assign tenant
        if tenant:
            user.tenant = tenant
        user.is_tenant_owner = True
        user.is_active = True
        user.is_tenant_staff = True
        user.save()

        # create profile (if not already)
        UserProfile.objects.get_or_create(user=user)

        return user

class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model"""
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'subdomain', 'email', 'phone', 
            'is_active', 'is_trial', 'trial_ends_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class TenantAccountSerializer(AccountSerializer):
    """
    Account serializer with tenant info and roles
    Inherits from AccountSerializer to avoid duplication
    """
    tenant = TenantSerializer(read_only=True)

    class Meta(AccountSerializer.Meta):
        # extend base fields
        fields = AccountSerializer.Meta.fields + [
            'is_tenant_owner',
            'is_tenant_staff',
            'last_login',
            'tenant',
        ]
        read_only_fields = AccountSerializer.Meta.read_only_fields + ['last_login']


# merchant-specific serializer
class MerchantUserProfileSerializer(UserProfileSerializer):

    """
    Inherits from UserProfileSerializer
    Adds is_merchant_user field
    """
    is_merchant_user = serializers.SerializerMethodField()
    tenant = TenantSerializer(read_only=True)

    class Meta(UserProfileSerializer.Meta):
        # extend fields from base
        fields = UserProfileSerializer.Meta.fields + ['is_merchant_user','tennant']
        read_only_fields = ['id', 'date_joined', 'tenant']
        
    def get_is_merchant_user(self, obj):
        # obj is UserProfile instance; check if related user has tenant
        return obj.user.tenant is not None
    
class SubscriptionSerializer(serializers.Serializer):
    """Serializer for subscription information"""
    status = serializers.CharField(read_only=True)
    trial_ends_at = serializers.DateTimeField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    stripe_customer_id = serializers.CharField(read_only=True)
    stripe_subscription_id = serializers.CharField(read_only=True)
    plan_name = serializers.CharField(read_only=True)
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if isinstance(instance, Tenant):
            data.update({
                'status': 'trial' if instance.is_trial else 'active',
                'trial_ends_at': instance.trial_ends_at,
                'is_paid': instance.is_paid,
                'stripe_customer_id': instance.stripe_customer_id,
                'stripe_subscription_id': instance.stripe_subscription_id,
                'plan_name': 'Basic Plan'  # You can make this dynamic
            })
        return data
