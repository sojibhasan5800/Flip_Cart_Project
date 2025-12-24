# # delivery_system/consumers.py
# import json
# import pika
# from django.conf import settings
# from django.db import transaction
# from django_tenants.utils import tenant_context
# from .models import DeliveryTenant, DeliveryOrder, DeliveryTracking, DeliverySettings
# from orders.models import Order


# class MultiTenantDeliveryConsumer:
#     """
#     Multi-tenant RabbitMQ Consumer for handling payment completed events
#     and automatically creating delivery orders for respective tenants
#     """
    
#     def __init__(self):
#         self.connection = None
#         self.channel = None
    
#     def connect(self):
#         """Establish connection to RabbitMQ"""
#         credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
#         parameters = pika.ConnectionParameters(
#             host=settings.RABBITMQ_HOST,
#             port=settings.RABBITMQ_PORT,
#             virtual_host=settings.RABBITMQ_VHOST,
#             credentials=credentials,
#             heartbeat=600,
#             blocked_connection_timeout=300
#         )
        
#         self.connection = pika.BlockingConnection(parameters)
#         self.channel = self.connection.channel()
        
#         # Declare exchange and queue
#         self.channel.exchange_declare(
#             exchange=settings.RABBITMQ_EXCHANGE,
#             exchange_type='direct',
#             durable=True
#         )
        
#         self.channel.queue_declare(
#             queue='multi_tenant_delivery_queue',
#             durable=True
#         )
        
#         self.channel.queue_bind(
#             queue='multi_tenant_delivery_queue',
#             exchange=settings.RABBITMQ_EXCHANGE,
#             routing_key='payment.completed'
#         )
        
#         self.channel.basic_qos(prefetch_count=1)
    
#     def start_consuming(self):
#         """Start consuming messages from RabbitMQ"""
#         self.channel.basic_consume(
#             queue='multi_tenant_delivery_queue',
#             on_message_callback=self.process_message,
#             auto_ack=False
#         )
        
#         print(" [*] Multi-tenant Delivery Consumer started. Waiting for payment completed events...")
#         self.channel.start_consuming()
    
#     def process_message(self, ch, method, properties, body):
#         """
#         Process incoming RabbitMQ message for payment completed events
#         with multi-tenant support
#         """
#         try:
#             message = json.loads(body)
#             event_type = message.get('event_type')
#             tenant_schema = message.get('tenant_schema')
            
#             if event_type == 'payment.completed' and tenant_schema:
#                 self.handle_payment_completed(message, tenant_schema)
            
#             # Acknowledge message processing
#             ch.basic_ack(delivery_tag=method.delivery_tag)
            
#         except Exception as e:
#             print(f"Error processing delivery message: {e}")
#             # Reject message and don't requeue (send to dead letter queue)
#             ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
#     def handle_payment_completed(self, message, tenant_schema):
#         """
#         Handle payment completed event and create delivery order for specific tenant
#         """
#         order_id = message.get('order_id')
#         payment_id = message.get('payment_id')
        
#         print(f"Processing delivery for order {order_id} with payment {payment_id} for tenant {tenant_schema}")
        
#         try:
#             # Get tenant
#             tenant = DeliveryTenant.objects.get(schema_name=tenant_schema)
            
#             # Process in tenant context
#             with tenant_context(tenant):
#                 with transaction.atomic():
#                     # Get the order
#                     order = Order.objects.select_for_update().get(id=order_id, is_ordered=True)
                    
#                     # Check tenant settings for auto delivery creation
#                     try:
#                         settings = DeliverySettings.objects.get(tenant=tenant)
#                         if not settings.auto_create_delivery:
#                             print(f"Auto delivery creation disabled for tenant {tenant_schema}")
#                             return
#                     except DeliverySettings.DoesNotExist:
#                         pass  # Continue with default behavior
                    
#                     # Check if delivery order already exists
#                     if hasattr(order, 'delivery_order'):
#                         print(f"Delivery order already exists for order {order_id} in tenant {tenant_schema}")
#                         return
                    
#                     # Extract delivery information from order
#                     district_name = order.state or 'Dhaka'
#                     area_name = order.city or 'Gulshan'
                    
#                     # Find delivery area for this tenant
#                     from .models import DeliveryArea, District, Division
                    
#                     try:
#                         # Try to find matching delivery area
#                         division = Division.objects.filter(
#                             tenant=tenant,
#                             name__icontains=district_name
#                         ).first()
                        
#                         if not division:
#                             # Use default division (Dhaka)
#                             division = Division.objects.filter(
#                                 tenant=tenant,
#                                 name='Dhaka'
#                             ).first()
                        
#                         district = District.objects.filter(
#                             tenant=tenant,
#                             division=division,
#                             name__icontains=district_name
#                         ).first()
                        
#                         if not district:
#                             # Use default district (Dhaka)
#                             district = District.objects.filter(
#                                 tenant=tenant,
#                                 division=division,
#                                 name='Dhaka'
#                             ).first()
                        
#                         delivery_area = DeliveryArea.objects.filter(
#                             tenant=tenant,
#                             district=district,
#                             area_name__icontains=area_name,
#                             is_available=True
#                         ).first()
                        
#                         if not delivery_area:
#                             # Use first available delivery area
#                             delivery_area = DeliveryArea.objects.filter(
#                                 tenant=tenant,
#                                 is_available=True
#                             ).first()
                            
#                     except Exception as e:
#                         print(f"Error finding delivery area: {e}")
#                         delivery_area = DeliveryArea.objects.filter(
#                             tenant=tenant,
#                             is_available=True
#                         ).first()
                    
#                     if not delivery_area:
#                         raise Exception(f"No available delivery area found for tenant {tenant_schema}")
                    
#                     # Calculate delivery charge
#                     delivery_charge = delivery_area.delivery_charge
#                     if order.order_total >= tenant.free_delivery_threshold:
#                         delivery_charge = 0.00
                    
#                     # Create delivery order
#                     from datetime import datetime, timedelta
#                     today = datetime.now().date()
#                     estimated_delivery_date = today + timedelta(days=delivery_area.min_delivery_days)
                    
#                     delivery_order = DeliveryOrder.objects.create(
#                         tenant=tenant,
#                         order=order,
#                         delivery_area=delivery_area,
#                         delivery_charge=delivery_charge,
#                         estimated_delivery_date=estimated_delivery_date,
#                         status='confirmed'
#                     )
                    
#                     # Create initial tracking record
#                     DeliveryTracking.objects.create(
#                         tenant=tenant,
#                         delivery_order=delivery_order,
#                         status='confirmed',
#                         description="Delivery order automatically created after successful payment"
#                     )
                    
#                     print(f"Successfully created delivery order: {delivery_order.delivery_id} for tenant {tenant_schema}")
                    
#                     # Send notification
#                     self.send_delivery_created_notification(delivery_order)
                
#         except DeliveryTenant.DoesNotExist:
#             print(f"Tenant {tenant_schema} not found")
#         except Order.DoesNotExist:
#             print(f"Order {order_id} not found or not completed in tenant {tenant_schema}")
#         except Exception as e:
#             print(f"Error creating delivery order for order {order_id} in tenant {tenant_schema}: {e}")
#             raise
    
#     def send_delivery_created_notification(self, delivery_order):
#         """
#         Send notification about delivery order creation based on tenant settings
#         """
#         try:
#             settings = DeliverySettings.objects.get(tenant=delivery_order.tenant)
#             if settings.send_delivery_notifications and settings.notify_on_creation:
#                 # Implement tenant-specific notification logic here
#                 print(f"Notification sent for delivery {delivery_order.delivery_id} in tenant {delivery_order.tenant.name}")
#         except DeliverySettings.DoesNotExist:
#             pass
    
#     def close(self):
#         """Close RabbitMQ connection"""
#         if self.connection:
#             self.connection.close()