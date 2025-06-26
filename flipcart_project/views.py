from django.shortcuts import render,redirect
from store.models import Product
import requests


def home(request,load_data_base =None):
    products = Product.objects.all().filter(is_available=True).order_by('created_date')
    # -------------- Api interogration ---------------
    if load_data_base is None: 
        return redirect('category_load')



    
    # URL = "https://dummyjson.com/products"
    #     response = requests.get(url=URL)
    #     data = response.json()
    # api_products = data.get('products',[])
    
    context ={
        'products':products,
        # 'api_products': api_products,
    }
    return render(request, 'home.html',context)