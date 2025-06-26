from django.shortcuts import render,redirect
import requests
from .models import Category
from django.utils.text import slugify

# Create your views here.
def load_category_object(request):
    category = 'https://dummyjson.com/products/categories'
    response = requests.get(url = category)
    category_list = response.json()
    
    for cat in category_list:
        slug_field = cat.get('slug', None)
        name_field = cat.get('name', None)
        url_field = cat.get('url', None)
        Category.objects.get_or_create(

            name = name_field,
            slug = slug_field,
            url = url_field,
        )
    return redirect('Product_load')
    



