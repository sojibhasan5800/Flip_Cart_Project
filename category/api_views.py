# category/api/views.py
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from .models import Category
from .serializers import CategorySerializer
import requests
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# ---------------------------
# Load categories from external API
# ---------------------------
class LoadCategoryAPIView(APIView):
    """
    GET: Load categories from https://dummyjson.com/products/categories
    - Creates new Category objects if not exists.
    - Returns list of loaded categories.
    """
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(operation_summary="Load categories from external API")
    def get(self, request):
        url = 'https://dummyjson.com/products/categories'
        response = requests.get(url=url)
        if response.status_code != 200:
            return Response({"error": "Failed to fetch categories"}, status=400)
        
        category_list = response.json()
        created = []
        for cat in category_list:
            slug_field = slugify(cat.get('slug') or cat)
            name_field = cat.get('name') or cat
            cat_obj, _ = Category.objects.get_or_create(
                category_name=name_field,
                slug=slug_field
            )
            created.append(cat_obj.category_name)
        return Response({"loaded_categories": created}, status=200)


# ---------------------------
# Category CRUD APIs
# ---------------------------
class CategoryListAPIView(generics.ListCreateAPIView):
    """
    GET: List all categories
    POST: Create new category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(operation_summary="List all categories")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Create new category")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve category by ID
    PUT: Update category
    DELETE: Delete category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(operation_summary="Retrieve category details")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update category")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Delete category")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
