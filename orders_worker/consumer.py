# import os, django, json, time
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flipcart_project.settings")
# django.setup()

# import pika
# from django.conf import settings
# from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer
# from seller_dashboard.models import SellerAnalytics
# from store.models import Product
# from orders.models import OrderProduct
# from collections import Counter
# from django.core.cache import cache

# credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
# params = pika.ConnectionParameters(host=settings.RABBITMQ_HOST, port=settings.RABBITMQ_PORT,
#                                    virtual_host=getattr(settings, 'RABBITMQ_VHOST', '/'),
#                                    credentials=credentials, heartbeat=600, blocked_connection_timeout=300)

# connection = pika.BlockingConnection(params)
# channel = connection.channel()
# channel.exchange_declare(exchange=settings.RABBITMQ_EXCHANGE, exchange_type='direct', durable=True)

# result = channel.queue_declare('', exclusive=True)  # temporary queue
# queue_name = result.method.queue
# channel.queue_bind(exchange=settings.RABBITMQ_EXCHANGE, queue=queue_name, routing_key='#')  # get all events

# channel.basic_qos(prefetch_count=1)
# channel_layer = get_channel_layer()

# def process_order_created(payload):
#     # payload contains items and seller_ids
#     seller_ids = payload.get('seller_ids', [])
#     for sid in seller_ids:
#         # recompute analytics for seller sid
#         order_products = OrderProduct.objects.filter(product__category__account_id=sid, ordered=True)
#         total_sales = sum([op.product_price * op.quantity for op in order_products])
#         total_orders = order_products.values('order').distinct().count()
#         total_items = sum([op.quantity for op in order_products])
#         top = Counter()
#         for op in order_products:
#             top[op.product.product_name] += op.quantity

#         products = Product.objects.filter(category__account_id=sid)
#         inventory = {str(p.id): {"name": p.product_name, "stock": p.stock} for p in products}

#         analytics, _ = SellerAnalytics.objects.update_or_create(
#             seller_id=sid,
#             defaults={
#                 "total_sales": total_sales,
#                 "total_orders": total_orders,
#                 "total_items_sold": total_items,
#                 "top_products": dict(top.most_common(10)),
#                 "inventory_summary": inventory
#             }
#         )
#         # update cache
#         data = {
#             'total_sales': analytics.total_sales,
#             'total_orders': analytics.total_orders,
#             'total_items_sold': analytics.total_items_sold,
#             'top_products': analytics.top_products,
#             'inventory_summary': analytics.inventory_summary,
#             'last_updated': analytics.last_updated.strftime("%Y-%m-%d %H:%M:%S")
#         }
#         cache.set(f"seller_analytics:{sid}", data, timeout=3600)
#         # push via channels
#         async_to_sync(channel_layer.group_send)(
#             f"seller_{sid}_dashboard",
#             {"type": "analytics_update", "data": data}
#         )

# def process_product_review(payload):
#     # for review, recalc top products by rating & qty (we'll reuse same aggregation)
#     product_id = payload.get('product_id')
#     # find seller of product
#     try:
#         prod = Product.objects.get(id=product_id)
#         sid = prod.category.account.id
#         # recompute analytics like above
#         process_order_created({"seller_ids":[sid]})
#     except Product.DoesNotExist:
#         pass

# def callback(ch, method, properties, body):
#     print(f"Received event: {payload}")
#     try:
#         payload = json.loads(body)
#     except Exception:
#         ch.basic_ack(delivery_tag=method.delivery_tag)
#         return

#     event_type = payload.get('event_type')
#     if event_type == 'order.created':
#         process_order_created(payload)
#     elif event_type == 'product.review':
#         process_product_review(payload)
#     else:
#         # optionally handle other event_types
#         pass

#     ch.basic_ack(delivery_tag=method.delivery_tag)

# print(" [*] orders_worker waiting for messages. To exit press CTRL+C")
# channel.basic_consume(queue=queue_name, on_message_callback=callback)
# channel.start_consuming()
