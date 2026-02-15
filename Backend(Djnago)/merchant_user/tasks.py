# seller_dashboard/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import connection,models
from django_tenants.utils import get_tenant_model
from datetime import timedelta
import json
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django_redis import get_redis_connection
from django_tenants.utils import schema_context


logger = logging.getLogger(__name__)

@shared_task(name='merchant_user.tasks.update_active_merchant_dashboards')
def update_active_merchant_dashboards():
    """
    প্রতি ১ মিনিটে চলবে (Celery Beat)
    শুধু active merchants (গত ২ মিনিটে dashboard-এ ছিল) এর জন্য
    """
    cutoff_time = timezone.now() - timedelta(minutes=2)

    TenantModel = get_tenant_model()
    active_tenants = TenantModel.objects.filter(
        last_dashboard_activity__gte=cutoff_time,
        is_verified=True,
        is_active=True
    ).distinct()

    if not active_tenants.exists():
        logger.info("No active merchants online — skipping update")
        return

    logger.info(f"Updating dashboard for {active_tenants.count()} active merchants")

    redis_conn = get_redis_connection("default")
    channel_layer = get_channel_layer()
    now = timezone.localtime()  # Current datetime
    current_minute = now.minute  # 0-59

    for tenant in active_tenants:
        try:
            with schema_context(tenant.schema_name):

                # এখানে তোমার ORM query বসবে
                payload = {
                    "totalProducts": 100,
                    "totalEarnings": 21,
                    "totalOrders": current_minute,
                    "recentReviews": [],
                    "updatedAt": timezone.now().isoformat()
                }
                # ✅ 1. Redis এ latest snapshot save
                redis_conn.set(
                    f"merchant:{tenant.id}:dashboard:latest",
                    json.dumps(payload),
                    ex=300  # 5 min TTL
                )

                # ✅ 2. WebSocket group এ পাঠাও
                async_to_sync(channel_layer.group_send)(
                    f"merchant_{tenant.id}",
                    {
                        "type": "dashboard_update",
                        "data": payload
                    }
                )
                logger.info(f"Dashboard updated for tenant {tenant.id}")


    
                # from store.models import Product
                # from orders.models import Order, OrderProduct
                # from store.models import ReviewRating

                # total_products = Product.objects.filter(is_available=True).count()

                # earnings = OrderProduct.objects.filter(
                #     order__is_ordered=True,
                #     order__status__in=['Completed', 'Delivered']
                # ).aggregate(
                #     total=models.Sum(models.F('product_price') * models.F('quantity'))
                # )['total'] or 0

                # total_orders = Order.objects.filter(is_ordered=True).count()

                # thirty_days_ago = timezone.now() - timedelta(days=30)
                # recent_reviews = ReviewRating.objects.filter(
                #     created_at__gte=thirty_days_ago,
                #     status=True
                # ).select_related('user', 'product')[:10]

                # reviews_data = [
                #     {
                #         "user": r.user.full_name() if r.user else "Anonymous",
                #         "rating": r.rating,
                #         "review": r.review,
                #         "subject": r.subject,
                #         "createdAt": r.created_at.isoformat()
                #     }
                #     for r in recent_reviews
                # ]

                # payload = {
                #     "totalProducts": total_products,
                #     "totalEarnings": float(earnings),
                #     "totalOrders": total_orders,
                #     "recentReviews": reviews_data,
                #     "updatedAt": timezone.now().isoformat()
                # }

        except Exception as e:
            logger.error(f"Error for tenant {tenant.schema_name}: {e}")