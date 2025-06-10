from django.contrib import admin
from .models import ChatMessage, Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'region', 'phone_number', 'is_complete', 'created_at']
    list_filter = ['is_complete', 'region', 'created_at']
    search_fields = ['user__username', 'user__email', 'region', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message_preview', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__username', 'message']
    readonly_fields = ['timestamp']
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message Preview'
