# chat/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r'chats', views.ChatViewSet, basename='chat')
# router.register(r'messages', views.MessageViewSet, basename='message') # Используем 'chats/pk/send_message' вместо этого

urlpatterns = [
    path('', include(router.urls)),
]