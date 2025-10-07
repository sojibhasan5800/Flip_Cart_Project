# Point: RabbitMQ publisher utility (orders/utils.py)
import json
import pika
import uuid
from django.conf import settings

def _get_connection():
    credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VHOST,
        credentials=credentials,
        heartbeat=600,  # adjust for env
        blocked_connection_timeout=300,
    )
    return pika.BlockingConnection(parameters)

def send_order_to_queue(message: dict):
    """ Point: publish a JSON message. Caller must call inside transaction.on_commit """
    conn = _get_connection()
    channel = conn.channel()
    # Declare exchange & queue and bind (idempotent)
    channel.exchange_declare(exchange=settings.RABBITMQ_EXCHANGE, exchange_type='direct', durable=True)
    channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True, arguments={
        # optional DLX config can be here
    })
    channel.queue_bind(queue=settings.RABBITMQ_QUEUE, exchange=settings.RABBITMQ_EXCHANGE, routing_key=settings.RABBITMQ_ROUTING_KEY)

    body = json.dumps(message, default=str)
    channel.basic_publish(
        exchange=settings.RABBITMQ_EXCHANGE,
        routing_key=settings.RABBITMQ_ROUTING_KEY,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent
            content_type='application/json',
            message_id=str(uuid.uuid4()),  # unique id for tracing
        )
    )
    print("cahnnel puclished")
    channel.close()
    conn.close()
