# store/api/serializers.py
from rest_framework import serializers
from .models import Product, ReviewRating, ProductGallery, Variation

class ProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(source='averageReview', read_only=True)
    review_count = serializers.IntegerField(source='countReview', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'product_name', 'slug', 'description', 'price', 'images',
            'stock', 'is_available', 'category', 'created_date', 'modified_date',
            'average_rating', 'review_count'
        ]
        read_only_fields = ['id', 'is_available', 'average_rating', 'review_count']

class ReviewRatingSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ReviewRating
        fields = ['id', 'product', 'user', 'user_name', 'subject', 'review', 'rating', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_name', 'created_at', 'updated_at']

class ProductGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductGallery
        fields = ['id', 'product', 'image']
        read_only_fields = ['id']

class VariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variation
        fields = ['id', 'product', 'variation_category', 'variation_value', 'is_active']
        read_only_fields = ['id']
