from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('complete_profile/', views.complete_profile, name='complete_profile'),
    path('chat/', views.chat_room, name='chat_room'),
    path('send_message/', views.send_message, name='send_message'),
    path('delete_message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('get_messages/', views.get_messages, name='get_messages'),
]
