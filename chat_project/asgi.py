import os
import django
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Import necessary modules for database interaction in consumer
from asgiref.sync import sync_to_async # Or from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from chat.models import Message # Assuming your Message model is in chat/models.py

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')
django.setup()

# Define the WebSocket Consumer Class
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
        
        # Get the user from the scope. If authenticated, use their username; otherwise, 'Anonymous'.
        user = self.scope['user']
        username = user.username if user.is_authenticated else 'Anonymous'

        # Save message to database only if the user is authenticated
        if user.is_authenticated:
            await self.save_message(user, self.room_name, message)
        else:
            print(f"Anonymous user '{username}' attempted to send message: '{message}' in room '{self.room_name}' (not saved to DB).")
            # You might want to send an error back to the client here for anonymous users.

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
            'username': event['username']
        }))

    # Method to save message to database asynchronously
    @sync_to_async # Or @database_sync_to_async if you prefer Channels' specific decorator
    def save_message(self, user, room_name, content):
        """
        Synchronously saves a chat message to the database.
        This method runs in a separate thread pool.
        """
        return Message.objects.create(
            sender=user,
            content=content,
            message_type='ROOM', # Explicitly set message_type for room messages
            room_name=room_name
        )

# Import websocket_urlpatterns from your chat app's routing.py
import chat.routing 

# Define ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(), # Handles standard HTTP requests
    "websocket": AuthMiddlewareStack( # Handles WebSocket connections with authentication
        URLRouter(
            chat.routing.websocket_urlpatterns # Routes WebSocket connections
        )
    ),
})