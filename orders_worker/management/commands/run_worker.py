# Point: Management command to run worker reliably
import json, time, sys
from django.core.management.base import BaseCommand
from django.conf import settings
import pika
from django.db import transaction
from orders.models import Order, Payment, OrderProduct
from carts.models import CartItem
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = "Run RabbitMQ order worker"

    def handle(self, *args, **options):
        credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        params = pika.ConnectionParameters(host=settings.RABBITMQ_HOST, port=settings.RABBITMQ_PORT,                                   
                                           virtual_host=settings.RABBITMQ_VHOST, credentials=credentials,
                                           heartbeat=600, blocked_connection_timeout=300)
        while True:
            try:
                conn = pika.BlockingConnection(params)
                channel = conn.channel()
                channel.exchange_declare(exchange=settings.RABBITMQ_EXCHANGE, exchange_type='direct', durable=True)

                # Point: declare queue with DLX & max-length or TTL if you want
                args = {
                    # 'x-dead-letter-exchange': 'orders_dlx',  # optional
                }
                channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True, arguments=args)
                channel.queue_bind(queue=settings.RABBITMQ_QUEUE, exchange=settings.RABBITMQ_EXCHANGE, routing_key=settings.RABBITMQ_ROUTING_KEY)

                channel.basic_qos(prefetch_count=1)

                def callback(ch, method, properties, body):
                    try:
                        payload = json.loads(body)
                        idemp_key = payload.get('idempotency_key') or payload.get('order_number')
                        order_id = payload.get('order_id')

                        # Idempotency check
                        try:
                            order = Order.objects.get(id=order_id)
                        except Order.DoesNotExist:
                            # log & ack to drop invalid order
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            return

                        if order.is_ordered:
                            # already processed
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            return

                        # Process inside DB transaction for atomicity
                        with transaction.atomic():
                            # Create Payment record
                            payment = Payment.objects.create(
                                user=order.user,
                                payment_id=f"RMQ{int(time.time())}",
                                payment_method='RabbitMQAuto',
                                amount_paid=order.order_total,
                                status='Completed'
                            )
                            order.payment = payment
                            order.is_ordered = True
                            order.save()

                            # Move cart items -> OrderProduct and reduce stock
                            cart_items = CartItem.objects.filter(user=order.user)
                            for item in cart_items:
                                OrderProduct.objects.create(
                                    order=order,
                                    payment=payment,
                                    user=order.user,
                                    product=item.product,
                                    quantity=item.quantity,
                                    product_price=item.product.price,
                                    ordered=True
                                )
                                # stock adjust
                                p = Product.objects.select_for_update().get(id=item.product.id)
                                if p.stock < item.quantity:
                                    raise Exception(f"Not enough stock for product {p.id}")
                                p.stock -= item.quantity
                                p.save()
                            cart_items.delete()

                        # Send confirmation email (outside heavy lock ideally)
                        try:
                            mail_subject = 'Your order is confirmed'
                            message = render_to_string('orders/order_recieved_email.html', {'user': order.user, 'order': order})
                            EmailMessage(mail_subject, message, to=[order.user.email]).send()
                        except Exception as e:
                            # non-fatal: log error
                            print("Email send failed:", e)

                        # ---- Add this block before ch.basic_ack ----
                        try:
                            channel_exchange = settings.RABBITMQ_EXCHANGE
                            event_channel = ch  # use same channel safely
                            event_payload = {
                                "event_type": "order.created",
                                "order_id": order.id,
                                "seller_ids": list(
                                    set(OrderProduct.objects.filter(order=order)
                                        .values_list("product__category__account_id", flat=True))
                                ),
                                "timestamp": time.time()
                            }
                            event_channel.basic_publish(
                                exchange=channel_exchange,
                                routing_key="order.created",
                                body=json.dumps(event_payload),
                                properties=pika.BasicProperties(delivery_mode=2)
                            )
                            print("[x] Published order.created event to exchange.")
                        except Exception as e:
                            print("Event publish failed:", e)

                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        # log error, and reject/requeue or send to DLX based on policy
                        print("Worker error:", e)
                        # requeue or nack without requeue (send to DLX)
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_consume(queue=settings.RABBITMQ_QUEUE, on_message_callback=callback)
                print(" [*] Worker started. Waiting for messages.")
                channel.start_consuming()

            except pika.exceptions.AMQPConnectionError as e:
                print("Connection error, retrying in 5s...", e)
                time.sleep(5)
                continue
            except KeyboardInterrupt:
                try:
                    conn.close()
                except:
                    pass
                sys.exit(0)
