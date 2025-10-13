from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('start/', views.start_conversation, name='start_conversation'),
    path('send-message/', views.send_message_ajax, name='send_message_ajax'),
    path('search-users/', views.user_search_ajax, name='user_search_ajax'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('delete-conversation/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),
]
