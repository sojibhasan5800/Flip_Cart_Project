from rest_framework import serializers
from .models import Account,UserProfile
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.id')
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'address_line_1', 'address_line_2', 'city', 'state', 'country']


User = get_user_model()
class AccountSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email already registered.")]
    )
    class Meta:
        model = Account
        profile = UserProfileSerializer(required=False)
        fields = ['email', 'first_name', 'last_name','password', 'confirm_password']

        extra_kwargs = {
                'password': {'write_only': True},
                'username': {'read_only': True},  # Username will be auto-generated
            }
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        # Django built-in password validation (length, common password, etc.)
        validate_password(data['password'])
        return data

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        phone_number = validated_data.pop('phone_number', None)
        email = validated_data['email']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        password = validated_data['password']
        # phone_number = validated_data['phone_number']

        username = email.split("@")[0]  # Auto-generate username from email

        account = Account(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_number=phone_number
        )
        account.set_password(password)
        account.is_active =False # Require email verification
        account.save()
        UserProfile.objects.create(user=account, **profile_data)
        return account
        



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, trim_whitespace=False)
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(request=self.context.get('request'), email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.", code="authorization")
        if not user.is_active:
            raise serializers.ValidationError("Account is not active. Please verify your email.", code="authorization")

        attrs['user'] = user
        return attrs


        

    