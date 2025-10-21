
import json, time, sys
from django.core.management.base import BaseCommand
from django.conf import settings
import pika
from django.db import transaction
from orders.models import Order, OrderProduct, Payment
from carts.models import CartItem
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from seller_dashboard.models import SellerAnalytics

class Command(BaseCommand):
    help = "Run RabbitMQ order worker"

    def handle(self, *args, **options):
        credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        params = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host=settings.RABBITMQ_VHOST,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )

        while True:
            try:
                conn = pika.BlockingConnection(params)
                channel = conn.channel()

                # Exchange & Queue declare
                channel.exchange_declare(exchange=settings.RABBITMQ_EXCHANGE, exchange_type='direct', durable=True)
                channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
                channel.queue_bind(queue=settings.RABBITMQ_QUEUE, exchange=settings.RABBITMQ_EXCHANGE, routing_key=settings.RABBITMQ_ROUTING_KEY)
                channel.basic_qos(prefetch_count=1)

                print(" [*] RabbitMQ Worker started... Waiting for messages.")

                # Callback function
                def callback(ch, method, properties, body):
                    try:
                        payload = json.loads(body)
                        event_type = payload.get("event_type")

                        if event_type == "order.created":
                            # print("webscok")
                            self.process_order(payload)
                        elif event_type == "product.review":
                            self.process_review(payload)

                        # Message ack
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                    except Exception as e:
                        print("Worker Error:", e)
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_consume(queue=settings.RABBITMQ_QUEUE, on_message_callback=callback)
                channel.start_consuming()

            except pika.exceptions.AMQPConnectionError as e:
                print("Connection error, retrying in 5s...", e)
                time.sleep(5)
                continue
            except KeyboardInterrupt:
                conn.close()
                sys.exit(0)

    # -------- Order processing --------
    def process_order(self, payload):
        order_id = payload.get("order_id")
        try:
            order = Order.objects.get(id=order_id)
            if order.is_ordered:
                return
        except Order.DoesNotExist:
            print(f"Order {order_id} does not exist")
            return

        with transaction.atomic():
            # Payment create
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

            # Cart items -> OrderProduct & stock update
            cart_items = CartItem.objects.filter(user=order.user)
            for item in cart_items:
                op = OrderProduct.objects.create(
                    order=order,
                    payment=payment,
                    user=order.user,
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.price,
                    ordered=True
                )
                op.variations.set(item.variations.all())
                op.save()

                # Stock update
                p = Product.objects.select_for_update().get(id=item.product.id)
                if p.stock < item.quantity:
                    raise Exception( f" Not enough stock for product '{p.product_name}'. "                  
                                f"Only {p.stock} item(s) available."
                                )
                p.stock -= item.quantity
                p.save()
            cart_items.delete()

        # Send confirmation email
        self.send_order_email(order)

        # Update seller analytics
        self.update_seller_analytics(order)

        # Publish order.created event for other services
        self.publish_order_event(order)

    # -------- Email --------
    def send_order_email(self, order):
        try:
            subject = 'Your Order is Confirmed '
            message = render_to_string('orders/order_recieved_email.html', {'user': order.user, 'order': order})
            email = EmailMessage(subject, message, to=[order.user.email])
            email.content_subtype = "html"
            email.send(fail_silently=False)
        except Exception as e:
            print("Email sending failed:", e)

    # -------- Seller Analytics --------
    def update_seller_analytics(self, order):
        seller_ids = set(OrderProduct.objects.filter(order=order).values_list("product__category__account_id", flat=True))
        for seller_id in seller_ids:
            analytics, created = SellerAnalytics.objects.get_or_create(seller_id=seller_id)
            analytics.total_orders += 1
            analytics.total_sales += float(order.order_total)
            analytics.total_items_sold += sum(
                item.quantity for item in OrderProduct.objects.filter(order=order, product__category__account_id=seller_id)
            )

            # Top products
            for op in OrderProduct.objects.filter(order=order, product__category__account_id=seller_id):
                name = op.product.product_name
                analytics.top_products[name] = analytics.top_products.get(name, 0) + op.quantity

            # Inventory summary
            for op in Product.objects.filter(category__account_id=seller_id):
                analytics.inventory_summary[op.id] = {"name": op.product_name, "stock": op.stock}

            analytics.save()

    # -------- Publish order.created event --------
    def publish_order_event(self, order):
        try:
            channel_exchange = settings.RABBITMQ_EXCHANGE
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=settings.RABBITMQ_HOST, port=settings.RABBITMQ_PORT, virtual_host=settings.RABBITMQ_VHOST,
                                          credentials=pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD))
            )
            channel = connection.channel()
            event_payload = {
                "event_type": "order.created",
                "order_id": order.id,
                "seller_ids": list(
                    set(OrderProduct.objects.filter(order=order)
                        .values_list("product__category__account_id", flat=True))
                ),
                "timestamp": time.time()
            }
            channel.basic_publish(
                exchange=channel_exchange,
                routing_key="order.created",
                body=json.dumps(event_payload),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()
            print("[x] Published order.created event to exchange.")
        except Exception as e:
            print("Event publish failed:", e)

    # -------- Review processing --------
    def process_review(self, payload):
        try:
            from store.models import ReviewRating
            review, created = ReviewRating.objects.get_or_create(
                user_id=payload.get("user_id"), 
                product_id=payload.get("product_id"),
                defaults={"rating": payload.get("rating"), "subject": "", "review": "", "status": True}
            )
            if not created:
                review.rating = payload.get("rating")
                review.save()
        except Exception as e:
            print("Review processing failed:", e)
