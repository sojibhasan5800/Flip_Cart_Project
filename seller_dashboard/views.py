# seller_dashboard/views.py
from django.shortcuts import render
from orders.models import OrderProduct
from .models import SellerAnalytics
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def dashboard(request):
    seller = request.user
    analytics = SellerAnalytics.objects.filter(seller=seller)

    context = {
        'analytics': analytics
    }
    return render(request, 'seller_dashboard/dashboard.html', context)

# AJAX endpoint for live update
@login_required
def dashboard_ajax(request):
    seller = request.user
    analytics = SellerAnalytics.objects.filter(seller=seller).values(
        'product__product_name','total_orders','total_revenue'
    )
    return JsonResponse(list(analytics), safe=False)
