import json
from kafka import KafkaConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

consumer = KafkaConsumer(
    'dashboard_topic',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

channel_layer = get_channel_layer()

def consume_kafka():
    # Listen to Kafka and broadcast updates to WebSocket
    for message in consumer:
        data = message.value
        async_to_sync(channel_layer.group_send)(
            "dashboard_group",
            {
                "type": "dashboard_update",
                "data": data
            }
        )
