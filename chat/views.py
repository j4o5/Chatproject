from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.db import models
from django.utils import timezone
import json
from .models import Profile, ChatMessage

def home(request):
    if request.user.is_authenticated:
        return redirect('chat_room')
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('chat_room')
        else:
            messages.error(request, 'Invalid login')
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Account created! Please login.')
            return redirect('login')
    
    return render(request, 'signup.html')

@login_required
def chat_room(request):
    # Get messages that are either public OR private messages involving current user
    messages = ChatMessage.objects.filter(
        is_deleted=False  # Don't show deleted messages
    ).filter(
        models.Q(is_private=False) |  # Public messages
        models.Q(user=request.user, is_private=True) |  # Messages sent by current user
        models.Q(recipient=request.user, is_private=True)  # Messages sent to current user
    )[:50]
    
    # Get all users for private messaging dropdown
    users = User.objects.exclude(id=request.user.id)
    
    return render(request, 'room.html', {'messages': messages, 'users': users})

@login_required
def complete_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        region = request.POST.get('region')
        phone_number = request.POST.get('phone_number')
        if region and phone_number:
            profile.region = region
            profile.phone_number = phone_number
            profile.save()
            messages.success(request, 'Profile updated!')
            return redirect('chat_room')
    return render(request, 'complete_profile.html', {'profile': profile})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def send_message(request):
    if request.method == 'POST':
        message_text = request.POST.get('message', '')
        recipient_id = request.POST.get('recipient_id')
        uploaded_file = request.FILES.get('file')
        
        # Must have either message or file
        if not message_text and not uploaded_file:
            return JsonResponse({'success': False, 'error': 'Message or file required'})
        
        # Create the message
        message_obj = ChatMessage.objects.create(
            user=request.user, 
            message=message_text,
            file=uploaded_file,
            file_name=uploaded_file.name if uploaded_file else ''
        )
        
        # If recipient is specified, make it private
        if recipient_id:
            try:
                recipient = User.objects.get(id=recipient_id)
                message_obj.recipient = recipient
                message_obj.is_private = True
                message_obj.save()
            except User.DoesNotExist:
                pass
        
        return JsonResponse({'success': True})

@login_required
def delete_message(request, message_id):
    if request.method == 'POST':
        message = get_object_or_404(ChatMessage, id=message_id, user=request.user)
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def get_messages(request):
    # Get messages that current user can see
    messages = ChatMessage.objects.filter(
        is_deleted=False  # Don't show deleted messages
    ).filter(
        models.Q(is_private=False) |  # Public messages
        models.Q(user=request.user, is_private=True) |  # Messages sent by current user
        models.Q(recipient=request.user, is_private=True)  # Messages sent to current user
    )[:50]
    
    data = []
    for m in messages:
        message_data = {
            'id': m.id,
            'user': m.user.username, 
            'message': m.message, 
            'timestamp': m.timestamp.strftime('%H:%M'),
            'is_private': m.is_private,
            'can_delete': m.user == request.user,
            'has_file': bool(m.file),
            'file_url': m.file.url if m.file else None,
            'file_name': m.file_name,
            'file_type': m.get_file_type(),
            'file_size': m.get_file_size()
        }
        
        if m.is_private and m.recipient:
            message_data['recipient'] = m.recipient.username
            
        data.append(message_data)
    
    return JsonResponse({'messages': data})
