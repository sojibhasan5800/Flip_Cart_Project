from rest_framework import serializers

from orders_management.models.address import ShippingAddress


class ShippingAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShippingAddress
        fields = '__all__'
        read_only_fields = [
            'id',
            'user',
            'created_at',
            'updated_at'
        ]