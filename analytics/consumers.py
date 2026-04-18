import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AnalyticsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("Attempting to connect to WebSocket...")
        # We get the user from the middleware (AuthMiddlewareStack)
        self.user = self.scope["user"]

        if self.user.is_authenticated:
            self.group_name = f"user_{self.user.id}"

            # Join the user's private group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
        else:
            # Reject the connection if not logged in
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # This method receives messages from the Group (sent by Celery)
    async def click_update(self, event):
        # Send the data to the Browser
        await self.send(text_data=json.dumps({
            "type": "click_update",
            "link_id": event["link_id"],
            "total_clicks": event["total_clicks"]
        }))