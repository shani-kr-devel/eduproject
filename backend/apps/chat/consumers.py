import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Conversation, Message
from .serializers import MessageSerializer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """One room per Conversation.pk. Connection is rejected unless the
    authenticated user (resolved by JWTAuthMiddleware) is a participant -
    the conversation id in the URL is never trusted on its own."""

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        user = self.scope["user"]

        if not user.is_authenticated or not await self.is_participant(user, self.conversation_id):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        text = (content.get("text") or "").strip()
        if not text:
            return
        user = self.scope["user"]
        message = await self.save_message(user, self.conversation_id, text)
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def is_participant(self, user, conversation_id):
        return Conversation.objects.filter(pk=conversation_id, participants=user).exists()

    @database_sync_to_async
    def save_message(self, user, conversation_id, text):
        message = Message.objects.create(conversation_id=conversation_id, sender=user, text=text)
        return MessageSerializer(message).data
