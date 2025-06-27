from rest_framework import serializers
from .models import Product
from .models import ReviewRating

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_date', 'modified_date', 'slug', 'is_available']



class ReviewRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewRating
        fields = '__all__'
        read_only_fields = ['user', 'ip', 'created_at', 'updated_at']

