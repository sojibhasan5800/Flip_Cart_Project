# store/api/serializers.py
from rest_framework import serializers
from store.models import Product,ProductGallery
from category.models import Category
from django.utils.text import slugify

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

        product = Product.objects.create(
            **validated_data,
            category=category,
            organization=organization,
            images=main_image_url,
            stock=0  # default stock
        )

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



















