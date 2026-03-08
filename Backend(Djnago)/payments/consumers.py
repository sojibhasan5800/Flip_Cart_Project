# billing/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SubscriptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.org_id = self.scope['url_route']['kwargs']['org_id']
        self.group_name = f"subscription_{self.org_id}"

        # Join group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from group
    async def subscription_update(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))