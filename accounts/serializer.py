from rest_framework import serializers
from .models import Account,UserProfile

class AccountSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    class Meta:
        model = Account
        fields = ['email', 'first_name', 'last_name','password', 'confirm_password','phone_number']
        extra_kwargs = {
                'password': {'write_only': True},
                'username': {'read_only': True},  # Username will be auto-generated
            }
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        if Account.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email Already Exits!")
        return data

    def create(self, validated_data):
        email = validated_data['email']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        password = validated_data['password']
        phone_number = validated_data['phone_number']

        username = email.split("@")[0]  # Auto-generate username from email

        account = Account(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_number=phone_number
        )
        account.set_password(password)
        account.is_active =False
        account.save()
        return account
        



class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(many=False)
    class Meta:
        model = UserProfile
        fields = '__all__'