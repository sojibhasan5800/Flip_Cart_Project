# accounts/api/serializers.py
from rest_framework import serializers
from .models import Account, UserProfile
from django.contrib.auth import authenticate

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
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        # username derived from email local-part (same as original view)
        email = validated_data['email']
        username = email.split('@')[0]
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
    userprofile = UserProfileSerializer(source='userprofile', read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'date_joined', 'userprofile']
        read_only_fields = ['email', 'date_joined', 'id']
