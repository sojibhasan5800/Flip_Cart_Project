# from django.shortcuts import render,redirect
# from store.models import Product

# import requests


# def home(request):
#     products = Product.objects.all().filter(is_available=True).order_by('created_date')
#     # -------------- Api interogration ---------------
#     if not products.exists(): 
#         return redirect('category_load')
#     context ={
#         'products':products,
#     }
#     return render(request, 'home.html',context)

from django.shortcuts import render
from django_tenants.utils import get_tenant

def home(request):
    try:
        # Correct way to get tenant
        tenant = get_tenant(request)
        
        # Public schema এর জন্য home page
        if tenant.schema_name == 'public':
            return render(request, 'base.html', {
                'message': 'Welcome to FlipCart Public Portal'
            })
        
        # Tenant schema এর জন্য products show করবে
        from store.models import Product
        products = Product.objects.filter(is_available=True)[:12]
        
        return render(request, 'home.html', {'products': products, 'tenant': tenant})
        
    except Exception as e:
        # Fallback যদি কোনো error হয়
        return render(request, 'public/home.html', {
            'message': f'Welcome to FlipCart - Error: {str(e)}'
        })