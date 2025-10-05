from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class SellerDashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return
        self.group_name = f"seller_{user.id}_dashboard"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # handler for messages sent by worker
    async def analytics_update(self, event):
        data = event.get('data', {})
        await self.send(json.dumps({
            'type': 'analytics.update',
            'data': data
        }))
