import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Add client to dashboard group
        await self.channel_layer.group_add("dashboard_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Remove client from group
        await self.channel_layer.group_discard("dashboard_group", self.channel_name)

    async def dashboard_update(self, event):
        # Receive event from group and send to WebSocket
        data = event['data']
        await self.send(text_data=json.dumps(data))
