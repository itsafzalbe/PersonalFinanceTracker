from django.contrib import admin
from .models import SuppportMessage


@admin.register(SuppportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'message_preview', 'is_admin_reply', 'is_read', 'created_at']
    list_filter = ['is_admin_reply', 'is_read', 'created_at']
    search_fields = ['message', 'user__username']
    readonly_fields = ['created_at']
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'



