# from rest_framework import serializers
# from .models import Order, OrderProduct, Payment
# from accounts.models import Account
# from store.models import Product, Variation

# class PaymentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Payment
#         fields = ['id', 'user', 'payment_id', 'payment_method', 'amount_paid', 'status', 'created_at']

# class OrderProductSerializer(serializers.ModelSerializer):
#     product_name = serializers.CharField(source='product.product_name', read_only=True)
#     variations = serializers.SlugRelatedField(
#         many=True, 
#         read_only=True,
#         slug_field='variation_value'
#     )

#     class Meta:
#         model = OrderProduct
#         fields = ['id', 'order', 'payment', 'user', 'product', 'product_name', 'variations', 'quantity', 'product_price', 'ordered', 'created_at']

# class OrderSerializer(serializers.ModelSerializer):
#     user_email = serializers.EmailField(source='user.email', read_only=True)
#     payment_detail = PaymentSerializer(source='payment', read_only=True)
#     order_products = OrderProductSerializer(many=True, source='orderproduct_set', read_only=True)

#     class Meta:
#         model = Order
#         fields = [
#             'id', 'user', 'user_email', 'payment', 'payment_detail', 'order_number', 'first_name', 'last_name',
#             'phone', 'email', 'address_line_1', 'address_line_2', 'country', 'state', 'city', 
#             'order_note', 'order_total', 'tax', 'status', 'ip', 'is_ordered', 'created_at', 'updated_at',
#             'order_products'
#         ]
#         read_only_fields = ['order_number', 'is_ordered', 'created_at', 'updated_at']
