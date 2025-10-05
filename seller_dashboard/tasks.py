from celery import shared_task
from django.contrib.auth import get_user_model
from orders.models import OrderProduct, Order
from store.models import Product
from .models import SellerAnalytics
from django.core.cache import cache
from collections import Counter
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

User = get_user_model()

@shared_task
def update_all_seller_analytics():
    sellers = User.objects.filter(is_staff=False, is_superuser=False)
    channel_layer = get_channel_layer()
    for seller in sellers:
        # Orders where seller's products were sold
        order_products = OrderProduct.objects.filter(product__category__account=seller, ordered=True)
        total_sales = sum([op.product_price * op.quantity for op in order_products])
        total_orders = order_products.values('order').distinct().count()
        total_items_sold = sum([op.quantity for op in order_products])
        top = Counter()
        for op in order_products:
            top[op.product.product_name] += op.quantity

        # Inventory summary for this seller (list of products and their current stock)
        products = Product.objects.filter(category__account=seller)
        inventory = {}
        for p in products:
            inventory[str(p.id)] = {"name": p.product_name, "stock": p.stock}

        analytics, _ = SellerAnalytics.objects.update_or_create(
            seller=seller,
            defaults={
                'total_sales': total_sales,
                'total_orders': total_orders,
                'total_items_sold': total_items_sold,
                'top_products': dict(top.most_common(10)),
                'inventory_summary': inventory
            }
        )
        # update cache for fast API
        cache_key = f"seller_analytics:{seller.id}"
        data = {
            'total_sales': analytics.total_sales,
            'total_orders': analytics.total_orders,
            'total_items_sold': analytics.total_items_sold,
            'top_products': analytics.top_products,
            'inventory_summary': analytics.inventory_summary,
            'last_updated': analytics.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        }
        cache.set(cache_key, data, timeout=3600)

        # Push via channel layer to connected clients (live)
        async_to_sync(channel_layer.group_send)(
            f"seller_{seller.id}_dashboard",
            {
                "type": "analytics_update",
                "data": data
            }
        )
