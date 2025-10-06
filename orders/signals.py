# from kafka import KafkaProducer
# import json
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import OrderProduct

# producer = KafkaProducer(
#     bootstrap_servers='localhost:9092',
#     value_serializer=lambda v: json.dumps(v).encode('utf-8')
# )

# @receiver(post_save, sender=OrderProduct)
# def send_order_to_kafka(sender, instance, created, **kwargs):
#     if created:
#         data = {
#             'product_id': instance.product.id,
#             'product_name': instance.product.product_name,
#             'price': instance.product_price,
#             'rating': instance.rating,
#         }
#         producer.send('dashboard_topic', data)
