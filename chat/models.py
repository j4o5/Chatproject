from django.db import models
from django.contrib.auth.models import User
import os

def upload_to(instance, filename):
    return f'chat_files/{instance.user.username}/{filename}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    region = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        if self.region and self.phone_number:
            self.is_complete = True
        else:
            self.is_complete = False
        super().save(*args, **kwargs)

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)  # Make message optional for file-only messages
    timestamp = models.DateTimeField(auto_now_add=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='received_messages')
    is_private = models.BooleanField(default=False)
    
    # New fields for file sharing and deletion
    file = models.FileField(upload_to=upload_to, null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        if self.is_private and self.recipient:
            return f"{self.user.username} → {self.recipient.username}: {self.message[:50] if self.message else '[File]'}"
        return f"{self.user.username}: {self.message[:50] if self.message else '[File]'}"
    
    def get_file_type(self):
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                return 'image'
            elif ext in ['.pdf']:
                return 'pdf'
            elif ext in ['.doc', '.docx']:
                return 'document'
            elif ext in ['.mp3', '.wav', '.ogg']:
                return 'audio'
            elif ext in ['.mp4', '.avi', '.mov']:
                return 'video'
            else:
                return 'file'
        return None
    
    def get_file_size(self):
        if self.file:
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size // 1024} KB"
            else:
                return f"{size // (1024 * 1024)} MB"
        return None
