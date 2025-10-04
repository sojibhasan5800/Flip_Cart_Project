# seller_dashboard/tasks.py
from celery import shared_task
from .models import SellerAnalytics
from orders.models import OrderProduct

@shared_task
def update_seller_analytics():
    sellers = OrderProduct.objects.values_list('product__category__id', flat=True).distinct()
    for order in OrderProduct.objects.all():
        seller = order.product.category.seller  # ধরছি Category-তে seller field আছে
        obj, created = SellerAnalytics.objects.get_or_create(seller=seller, product=order.product)
        total_orders = OrderProduct.objects.filter(product=order.product, order__is_ordered=True).count()
        total_revenue = OrderProduct.objects.filter(product=order.product, order__is_ordered=True).aggregate(total=models.Sum('product_price'))['total'] or 0
        obj.total_orders = total_orders
        obj.total_revenue = total_revenue
        obj.save()
