# orders/api/serializers.py
from rest_framework import serializers
from .models import Payment, Order, OrderProduct
from store.serializers import ProductSerializer
from accounts.serializers import AccountSerializer
from store.models import Variation

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'payment_id', 'payment_method', 'amount_paid', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']

class OrderProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    variations = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field='variation_value'
    )

    class Meta:
        model = OrderProduct
        fields = ['id', 'order', 'payment', 'user', 'product', 'variations', 'quantity', 'product_price', 'ordered', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'ordered']

class OrderSerializer(serializers.ModelSerializer):
    user = AccountSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    ordered_products = OrderProductSerializer(many=True, source='orderproduct_set', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'payment', 'order_number', 'first_name', 'last_name', 'phone', 'email',
                  'address_line_1', 'address_line_2', 'country', 'state', 'city', 'order_note',
                  'order_total', 'tax', 'status', 'ip', 'is_ordered', 'created_at', 'updated_at',
                  'ordered_products']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_ordered', 'order_number', 'payment']
