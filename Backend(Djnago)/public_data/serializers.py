from store.serializers import ProductListSerializer
from rest_framework import serializers



# Extend the serializer to include organization details for global view
class GlobalProductSerializer(ProductListSerializer):
    organization = serializers.CharField(source='organization.business_name')
    organization_slug = serializers.CharField(source='organization.username')  # Assuming username is used for shop slugs

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ['organization', 'organization_slug']