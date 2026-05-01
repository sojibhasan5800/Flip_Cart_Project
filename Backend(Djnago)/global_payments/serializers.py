from rest_framework import serializers
from .models import SubscriptionPaymentTransaction

class SubscriptionPaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPaymentTransaction
        fields = '__all__'
        read_only_fields = ['transaction_id', 'status', 'created_at', 'updated_at']