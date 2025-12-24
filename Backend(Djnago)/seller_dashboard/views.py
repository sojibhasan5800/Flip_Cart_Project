from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import SellerAnalytics
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def dashboard(request):
    return render(request, 'seller_dashboard/dashboard.html')

@login_required
def dashboard_data_api(request):
    seller = request.user
    cache_key = f"seller_analytics:{seller.id}"
    data = cache.get(cache_key)
    if not data:
        # fallback to DB
        # analytics = SellerAnalytics.objects.filter(seller=seller).first()
        admin_user = User.objects.get(email='admin@gmail.com')
        analytics = SellerAnalytics.objects.filter(seller=admin_user).first()
        if analytics:
            data = {
                'total_sales': analytics.total_sales,
                'total_orders': analytics.total_orders,
                'total_items_sold': analytics.total_items_sold,
                'top_products': analytics.top_products,
                'inventory_summary': analytics.inventory_summary,
                'last_updated': analytics.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
            }
            cache.set(cache_key, data, timeout=300)  # 5 min cache
        else:
            data = {}
    return JsonResponse(data)
