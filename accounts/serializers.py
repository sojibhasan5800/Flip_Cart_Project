# accounts/api/serializers.py
from rest_framework import serializers
from .models import Account, UserProfile, Tenant
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import re

class MerchantRegistrationSerializer(serializers.Serializer):
    """Serializer for merchant registration"""
    
    # Business info
    business_name = serializers.CharField(max_length=100)
    subdomain = serializers.CharField(max_length=50)
    
    # Personal info
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_subdomain(self, value):
        """Validate subdomain format and availability"""
        # Check format (alphanumeric and hyphens only)
        if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', value):
            raise serializers.ValidationError(
                'Subdomain can only contain lowercase letters, numbers, and hyphens. Cannot start or end with hyphen.'
            )
        
        # Check reserved subdomains
        reserved = ['www', 'admin', 'api', 'blog', 'support', 'help', 'mail']
        if value in reserved:
            raise serializers.ValidationError('This subdomain is reserved. Please choose another one.')
        
        # Check length
        if len(value) < 3:
            raise serializers.ValidationError('Subdomain must be at least 3 characters long.')
        
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

class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model"""
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'subdomain', 'email', 'phone', 
            'is_active', 'is_trial', 'trial_ends_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class MerchantProfileSerializer(serializers.ModelSerializer):
    """Serializer for merchant profile"""
    
    tenant = TenantSerializer(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'is_tenant_owner', 'date_joined', 'tenant'
        ]
        read_only_fields = ['id', 'date_joined', 'tenant']






# ------------------------ previous ----------------------------

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    - Validates password confirmation
    - Creates Account + default UserProfile
    Security notes:
    - Do not return password fields in responses.
    - Enforce password validation at view or via validators if required.
    """
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        try:
            validate_email(data['email'])
        except ValidationError:
            raise serializers.ValidationError({"email": "Enter a valid email address."})
        
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        # username derived from email local-part (same as original view)
        email = validated_data['email']
        base_username = email.split('@')[0]
        username = base_username

        if Account.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email is already registered. Please login or use another email."})
        counter = 1
        while Account.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = Account.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=email,
            username=username,
            password=validated_data['password']
        )
        user.phone_number = validated_data.get('phone_number', '')
        user.save()
        # create user profile (keeps parity with MVT behaviour)
        UserProfile.objects.get_or_create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login endpoint. Authenticates via email + password.
    Returns user (read-only) and token will be created in the view.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        print(user)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User account is not active.")
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for profile editing and display.
    """
    class Meta:
        model = UserProfile
        fields = ['address_line_1', 'address_line_2', 'city', 'state', 'country', 'profile_picture']


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer for Account read operations (dashboard / profile responses).
    Avoids returning password and sensitive fields.
    """
    userprofile = UserProfileSerializer( read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'date_joined', 'userprofile']
        read_only_fields = ['email', 'date_joined', 'id']
