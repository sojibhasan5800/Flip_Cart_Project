from django.shortcuts import render,redirect
import requests
from .models import Category
from .serializers import CategorySerializer
from rest_framework import viewsets
from django.utils.text import slugify

# Create your views here.
#--------------------- Api Create -------------------------------------

# class CategoryViewSet(viewsets.ModelViewSet):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer

# ------------------------------------------------------------------------


def load_category_object(request):
    category = 'https://dummyjson.com/products/categories'
    response = requests.get(url = category)
    category_list = response.json()
    
    for cat in category_list:
        slug_field = cat.get('slug', None)
        name_field = cat.get('name', None)
        url_field = cat.get('url', None)
        Category.objects.get_or_create(
            category_name = name_field,
            slug = slug_field,
            url = url_field,
        )
    print("loaded category!!!!!!!!!")
    return redirect('Product_load')
    



