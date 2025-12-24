# # carts/api/serializers.py
# from rest_framework import serializers
# from .models import Cart, CartItem
# from store.serializers import ProductSerializer, VariationSerializer
# from accounts.serializers import AccountSerializer

# class CartSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Cart
#         fields = ['id', 'cart_id', 'date_added']

# class CartItemSerializer(serializers.ModelSerializer):
#     product = ProductSerializer(read_only=True)
#     variations = VariationSerializer(many=True, read_only=True)
#     user = AccountSerializer(read_only=True)
#     sub_total = serializers.SerializerMethodField()
#     cart_id = serializers.SerializerMethodField() 

#     class Meta:
#         model = CartItem
#         fields = ['id', 'user', 'product', 'variations', 'cart_id', 'quantity', 'is_active', 'sub_total']

#     def get_sub_total(self, obj):
#         return obj.sub_total()
    
#     def get_cart_id(self, obj):
#         return obj.cart.cart_id if obj.cart else None
