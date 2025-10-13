from django.contrib import admin
from .models import Conversation, Message, MessageReadStatus

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'get_participants', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'participants__username']
    filter_horizontal = ['participants']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_participants(self, obj):
        return ', '.join([user.username for user in obj.participants.all()])
    get_participants.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'created_at', 'is_read']
    list_filter = ['created_at', 'is_read', 'sender']
    search_fields = ['content', 'sender__username', 'conversation__title']
    readonly_fields = ['created_at', 'edited_at']
    raw_id_fields = ['conversation', 'sender']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'user', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'message__content']
    raw_id_fields = ['message', 'user']
