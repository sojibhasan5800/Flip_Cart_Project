# accounts/api/serializers.py
from sqlite3 import IntegrityError
from rest_framework import serializers
from .models import Account, UserProfile 
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
import re

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for profile editing and display.
    """
    class Meta:
        model = UserProfile
        fields = ['address_line_1', 'address_line_2', 'city', 'state', 'country', 'profile_picture']


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
        

        # counter = 1
        # while Account.objects.filter(username=username).exists():
        #     username = f"{base_username}{counter}"
        #     counter += 1
        

        counter = 1
        MAX_ATTEMPTS = 10

        while counter <= MAX_ATTEMPTS:
            try:              
                user = Account.objects.create_user(
                    first_name=validated_data['first_name'],
                    last_name=validated_data['last_name'],
                    email=email,
                    username=username,
                    password=validated_data['password'],
                    phone_number=validated_data.get('phone_number', '')
                )
                break  # success
            except IntegrityError as e:
                error_msg = str(e)
                print("IntegrityError caught!")
                print("Error message:", error_msg)

                # check which field caused the error
                if 'username' in error_msg:
                    print("Conflict field: username =", username)
                    username = f"{base_username}{counter}"
                    counter += 1
                elif 'email' in error_msg:
                    print("Conflict field: email =", email)
                    # email conflict হলে retry সম্ভব নয়, error raise করা
                    raise serializers.ValidationError({"email": "এই email ইতিমধ্যেই register করা হয়েছে।"})
                else:
                    # অন্য কোনো ডাটাবেস error
                    print("Other field conflict or DB error")
                    raise serializers.ValidationError({"error": "User create করতে সমস্যা।"})
     
                 

        # create user profile
        UserProfile.objects.get_or_create(user=user)
        return user
    # raise serializers.ValidationError({"username": "Could not generate a unique username. Please try again."})



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


class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    organization = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'date_joined',
            'roles',
            'organization',
            'profile',
        ]

    def get_roles(self, obj):
        return {
            "is_superadmin": obj.is_superadmin,
            "is_admin": obj.is_admin,
            "is_tenant_owner": obj.is_tenant_owner,
            "is_tenant_staff": obj.is_tenant_staff,
        }

    def get_organization(self, obj):
        if not obj.organization:
            return None
        return {
            "id": obj.organization.id,
            "name": obj.organization.business_name,
            "is_active": obj.organization.is_active,
        }
