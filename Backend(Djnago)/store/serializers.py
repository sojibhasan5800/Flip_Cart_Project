# store/api/serializers.py
from itertools import product
import json
from rest_framework import serializers
from store.models import Product,ProductGallery
from category.models import Category
from django.utils.text import slugify
from django_redis import get_redis_connection

class ProductSerializer(serializers.ModelSerializer):
    main_image_url = serializers.URLField(write_only=True, required=True)   # from frontend
    gallery_image_urls = serializers.ListField(                             # from frontend
        child=serializers.URLField(), write_only=True, required=False, default=[]
    )

    class Meta:
        model = Product
        fields = [
            'product_name', 'slug', 'description', 'price', 'stock', 'is_available',
            'category', 'organization',
            'main_image_url', 'gallery_image_urls'   # write-only
        ]
        read_only_fields = ['organization', 'slug']

    def create(self, validated_data):
        # Pop extra fields
        main_image_url = validated_data.pop('main_image_url')
        gallery_urls = validated_data.pop('gallery_image_urls', [])

        # Set main image URL
        validated_data['images'] = main_image_url

        product = Product.objects.create(**validated_data)

        # Create gallery entries
        for url in gallery_urls:
            ProductGallery.objects.create(product=product, images=url)

        return product
    
class ProductCreateSerializer(serializers.ModelSerializer):
    main_image_url = serializers.URLField(write_only=True)
    gallery_image_urls = serializers.ListField(
        child=serializers.URLField(), write_only=True, required=False, default=[]
    )
    category = serializers.CharField(write_only=True)

    class Meta:
        model = Product
        fields = [
            "product_name", "description", "mrp", "price", "category",
            "main_image_url", "gallery_image_urls"
        ]

    def validate(self, data):
        if data["price"] >= data["mrp"]:
            raise serializers.ValidationError("Offer price must be less than MRP")
        return data

    def create(self, validated_data):
        organization = self.context["organization"]

        main_image_url = validated_data.pop("main_image_url")
        gallery_urls = validated_data.pop("gallery_image_urls", [])

        # category handle
        category_name = validated_data.pop("category")
        category, _ = Category.objects.get_or_create(
            category_name=category_name,
            defaults={"slug": slugify(category_name)}
        )

        product = Product(
        **validated_data,
        category=category,
        organization=organization,
        images=main_image_url,
        )
        product.save()   # <-- এটা খুব জরুরি

        for url in gallery_urls:
            ProductGallery.objects.create(product=product, images=url)

        return product

class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.category_name")

    class Meta:
        model = Product
        fields = [
            "id",
            "product_name",
            "slug",
            "price",
            "mrp",
            "images",
            "stock",
            "is_available",
            "description",
            "category",
            "created_date",
        ]


class ProductHomeSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField()
    image = serializers.CharField(source='images')

    class Meta:
        model = Product
        fields = (
            'id',
            'product_name',
            'price',
            'average_rating',
            'image',
            'created_date',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    variations = serializers.SerializerMethodField()
    galleries = serializers.SerializerMethodField()
    gallery_count = serializers.IntegerField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "product_name", "slug", "description",
            "price", "mrp", "images", "stock", "is_available",
            "category", "organization", "variations",
            "galleries", "gallery_count", "reviews",
            "created_date", "modified_date"
        ]

    def get_category(self, obj):
        if obj.category:
            return {"id": obj.category.id, "name": obj.category.category_name}
        return None

    def get_organization(self, obj):
        org = obj.organization
        if org:
            return {
                "id": org.id,
                "username": org.username,
                "business_name": org.business_name,
                "store_logo": org.store_logo,
                "store_url": org.store_url,
            }
        return None

    def get_variations(self, obj):
        # Already prefetch_related + only used → no extra query
        return [{"variation_category": v.variation_category, "variation_value": v.variation_value} 
                for v in obj.variation_set.all()]

    def get_galleries(self, obj):
        # Only id & images are loaded
        return [{"id": g.id, "images": g.images} for g in obj.productgallery_set.all()]

    def get_gallery_count(self, obj):
        return getattr(obj, 'gallery_count', 0)

    # def get_reviews(self, obj):
    #     redis = get_redis_connection("default")
    #     cached = redis.get(f'product_reviews:{obj.id}')
    #     if cached:
    #         return json.loads(cached)
    #     return []
    def get_reviews(self, obj):
        return self.context.get("reviews", [])












