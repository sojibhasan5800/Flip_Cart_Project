# category/api/serializers.py
from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    - Used for API CRUD operations.
    """
    class Meta:
        model = Category
        fields = ['id', 'category_name', 'slug', 'url', 'description', 'cat_image', 'account']
        read_only_fields = ['id', 'account']
