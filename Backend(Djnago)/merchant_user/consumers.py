import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class MerchantDashboardConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.org_id = int(self.scope["url_route"]["kwargs"]["org_id"])
        self.group_name = f"merchant_{self.org_id}"

        # নিজের personal group-এ যোগ
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # সব মার্চেন্টের জন্য global group-এ যোগ (settings broadcast-এর জন্য)
        await self.channel_layer.group_add(
            "global_merchant_dashboard",
            self.channel_name
        )

        await self.accept()

        # প্রথমে Redis থেকে latest snapshot পাঠাও
        latest = await self.get_latest_data()
        if latest:
            await self.send(text_data=json.dumps({
                "type": "dashboard_update",
                "data": latest
            }))

        await self.update_activity()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        # global group থেকেও discard
        await self.channel_layer.group_discard(
            "global_merchant_dashboard",
            self.channel_name
        )


    async def dashboard_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "dashboard_update",
            "data": event["data"]
        }))

    # নতুন handler: scheduler settings broadcast এর জন্য
    async def scheduler_settings_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "scheduler_settings",
            "data": event["data"]
        }))


    async def receive(self, text_data):
        # প্রতি ping এ activity update হবে
        await self.update_activity()


    @database_sync_to_async
    def update_activity(self):
        from merchant_user.models import Organization

        Organization.objects.filter(
            id=self.org_id
        ).update(
            last_dashboard_activity=timezone.now()
        )


    @database_sync_to_async
    def get_latest_data(self):
        from django_redis import get_redis_connection

        redis = get_redis_connection("default")
        key = f"merchant:{self.org_id}:dashboard:latest"

        data = redis.get(key)

        if not data:
            return None

        return json.loads(data)