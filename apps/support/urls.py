from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('chat/', views.user_chat, name='user_chat'),
    
    path('admin/chats/', views.admin_chat_list, name='admin_chat_list'),
    path('admin/chat/<int:user_id>/', views.admin_chat_detail, name='admin_chat_detail'),
    path('api/unread/', views.get_unread_count, name='get_unread_count'),
]