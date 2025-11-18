# chat/serializers.py

from rest_framework import serializers
from .models import Chat, Message, ReadReceipt  # Додано імпорт ReadReceipt
from django.contrib.auth import get_user_model
from tasks.serializers import UserAssignedSerializer

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор для сообщений."""
    sender = UserAssignedSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'content', 'timestamp']
        read_only_fields = ['sender']


class ChatListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения списка чатов (кратко)."""
    participants = UserAssignedSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'title', 'is_group_chat', 'participants', 'created_at', 'last_message', 'unread_count']

    def get_last_message(self, obj):
        """Получает последнее сообщение в чате."""
        try:
            # 🛠️ ИСПРАВЛЕНИЕ 1: Использование 'messages' вместо 'message_set'
            message = obj.messages.latest('timestamp')
            return MessageSerializer(message).data
        except Message.DoesNotExist:
            return None

    def get_unread_count(self, chat):
        """Рассчитывает количество непрочитанных сообщений для текущего пользователя."""
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return 0

        try:
            receipt = ReadReceipt.objects.select_related('last_read_message').get(chat=chat, user=user)
        except ReadReceipt.DoesNotExist:
            receipt = None

        last_read_id = receipt.last_read_message.id if (receipt and receipt.last_read_message) else 0

        # 🛠️ ИСПРАВЛЕНИЕ 2: Использование 'messages' вместо 'message_set'
        unread_count = chat.messages.filter(
            id__gt=last_read_id,
        ).exclude(sender=user).count()

        return unread_count


class ChatDetailSerializer(ChatListSerializer):
    """Сериализатор для детального просмотра чата (включает историю сообщений)."""
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ChatListSerializer.Meta):
        fields = ChatListSerializer.Meta.fields + ['messages']