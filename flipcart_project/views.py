from django.shortcuts import render,redirect
from store.models import Product
import requests


def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('created_date')
    # -------------- Api interogration ---------------
    # if not products.exists(): 
    #     return redirect('category_load')
    context ={
        'products':products,
    }
    return render(request, 'home.html',context)