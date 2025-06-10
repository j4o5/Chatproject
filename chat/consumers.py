# chat/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from channels.db import database_sync_to_async # Recommended for DB operations in Channels
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get room name from URL route
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # Create a unique group name for the room
        self.room_group_name = f'chat_{self.room_name}'

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial connection message to the client
        # Note: You might want to refine this message or send it only on successful connection.
        await self.send(text_data=json.dumps({"message": "WebSocket connected!", "username": "System"}))

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        # Get the user from the scope.
        # self.scope['user'] is available if you're using AuthMiddlewareStack in your asgi.py
        user = self.scope['user']
        username = user.username if user.is_authenticated else 'Anonymous'

        # Save message to database only if the user is authenticated
        if user.is_authenticated:
            await self.save_message(user, self.room_name, message)
        else:
            print(f"Anonymous user '{username}' attempted to send message: '{message}' in room '{self.room_name}' (not saved to DB).")
            # Consider sending an error message back to the client for unauthenticated users.

        # Broadcast message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username, # Send the actual username
            }
        )

    # Receive message from group (This method is called when a message is sent to the group)
    async def chat_message(self, event):
        # Send the received message and username back to the WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'] # No need for .get() with default if 'username' is always sent
        }))

    @database_sync_to_async
    def save_message(self, user, room_name, content):
        """
        Synchronously saves a chat message to the database.
        This method runs in a separate thread pool thanks to @database_sync_to_async.
        """
        return Message.objects.create(
            sender=user,
            content=content,
            message_type='ROOM', # Explicitly set message_type for room messages
            room_name=room_name
        )