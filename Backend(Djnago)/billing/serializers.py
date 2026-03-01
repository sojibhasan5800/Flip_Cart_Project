

# billing/serializers.py (For API responses, extensible)
from rest_framework import serializers

from merchant_user.models import Organization
from .models import SubscriptionPlan, OrganizationSubscription, ProductBoostSubscription, Invoice

class OrganizationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'business_name']
        
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OrganizationSubscriptionSerializer(serializers.ModelSerializer):
        organization = OrganizationSimpleSerializer(read_only=True)
        organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), source='organization', write_only=True
        )
        plan = SubscriptionPlanSerializer(read_only=True)


        class Meta:
            model = OrganizationSubscription
            fields = '__all__'
            read_only_fields = ['start_date', 'end_date', 'status', 'created_at', 'updated_at']

class ProductBoostSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductBoostSubscription
        fields = '__all__'
        read_only_fields = ['boost_start_date', 'boost_end_date', 'is_active', 'created_at', 'updated_at']

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'status', 'issued_at', 'due_at', 'paid_at', 'created_at', 'updated_at']

