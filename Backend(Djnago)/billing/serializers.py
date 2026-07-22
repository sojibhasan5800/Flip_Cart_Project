

# billing/serializers.py (For API responses, extensible)
from rest_framework import serializers
import stripe

from merchant_user.models import Organization
from .models import SubscriptionPlan, OrganizationSubscription, ProductBoostSubscription,CustomerSubscription
from global_payments.models import Invoice

class OrganizationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'business_name']
        
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # interval_map = {
        #     "monthly": "month",
        #     "yearly": "year",
        #     "weekly": "week",
        #     "daily": "day",
        # }
        billing_cycle = validated_data.get("billing_cycle", "monthly")
        
        if billing_cycle == "7_days":
            recurring = {
                "interval": "day",
                "interval_count": 7,
            }

        elif billing_cycle == "15_days":
            recurring = {
                "interval": "day",
                "interval_count": 15,
            }

        elif billing_cycle == "monthly":
            recurring = {
                "interval": "month",
                "interval_count": 1,
            }

        elif billing_cycle == "quarterly":
            recurring = {
                "interval": "month",
                "interval_count": 3,
            }

        elif billing_cycle == "half_yearly":
            recurring = {
                "interval": "month",
                "interval_count": 6,
            }

        elif billing_cycle == "yearly":
            recurring = {
                "interval": "year",
                "interval_count": 1,
            }

        else:
            raise serializers.ValidationError(
                {
                    "billing_cycle": "Invalid billing cycle"
                }
            )
            
        # stripe_interval = interval_map.get(billing_cycle)
        # if not stripe_interval:
        #     raise serializers.ValidationError({"billing_cycle": "Invalid billing cycle"})

        # Stripe Product তৈরি
        product = stripe.Product.create(
            name=validated_data['name'],
            description=f"{validated_data['plan_level'].title()} {validated_data['plan_type']} plan",
        )

        # Stripe Price তৈরি
        unit_amount = int(validated_data['price'] * 100)  # cents এ
        price = stripe.Price.create(
            unit_amount=unit_amount,
            currency=validated_data['currency'].lower(),
            recurring=recurring,  # ✅ map করা value ব্যবহার
            product=product.id
        )

        validated_data['stripe_price_id'] = price.id
        # validated_data['stripe_product_id'] = product.id  # optional, save করলে পরে use করতে পারবেন

        return super().create(validated_data)

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

class PlusMembershipPlanSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "plan_name",
            "slug",
            "plan_level",
            "price",
            "currency",
            "billing_cycle",
            "duration_days",
            "features",
        ]  
        
class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_number', 'status', 'issued_at', 'due_at', 'paid_at', 'created_at', 'updated_at']

