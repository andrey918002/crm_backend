# chat/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db import models
from django.db.models import Q
from django.http import Http404
from .models import Chat, Message, ReadReceipt  # Додано імпорт ReadReceipt
from .serializers import ChatListSerializer, ChatDetailSerializer, MessageSerializer
from .permissions import IsParticipant
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatViewSet(viewsets.ModelViewSet):
    """
    API для управления чат-комнатами и сообщениями.
    """
    permission_classes = [permissions.IsAuthenticated, IsParticipant]

    def get_queryset(self):
        """Пользователь видит только те чаты, в которых он участвует."""
        user = self.request.user
        return Chat.objects.filter(participants=user).order_by('-created_at').distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatListSerializer
        return ChatDetailSerializer

    def perform_create(self, serializer):
        participants_data = self.request.data.get('participants')
        if not participants_data or len(participants_data) == 0:
            raise Exception("Участники не указаны.")

        participants_ids = set(participants_data)
        participants_ids.add(self.request.user.id)

        if len(participants_ids) == 2 and not self.request.data.get('is_group_chat'):
            existing_chats = Chat.objects.filter(
                is_group_chat=False,
                participants__id__in=participants_ids
            ).annotate(p_count=models.Count('participants')).filter(p_count=2)

            if existing_chats.exists():
                return existing_chats.first()

        chat = serializer.save(is_group_chat=len(participants_ids) > 2 or self.request.data.get('is_group_chat', False))
        chat.participants.set(participants_ids)
        return chat

    # ACTION: Позначити всі повідомлення в чаті як прочитані
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsParticipant])
    def mark_as_read(self, request, pk=None):
        try:
            chat = self.get_object()
        except Http404:
            return Response({'detail': 'Чат не знайдено.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # 🛠️ ИСПРАВЛЕНИЕ 3: Использование 'messages' вместо 'message_set'
        last_message = chat.messages.filter(sender__isnull=False).order_by('-timestamp').first()

        if not last_message:
            return Response({'detail': 'У цьому чаті немає повідомлень.'}, status=status.HTTP_204_NO_CONTENT)

        # Створюємо або оновлюємо ReadReceipt
        receipt, created = ReadReceipt.objects.update_or_create(
            chat=chat,
            user=user,
            defaults={'last_read_message': last_message}
        )

        return Response({
            'detail': f'Чат {pk} позначено як прочитаний.',
            'last_read_message_id': last_message.id
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """REST-эндпоинт для отправки сообщения (используется как резерв или для проверки)."""
        chat = self.get_object()

        if request.user not in chat.participants.all():
            return Response({"detail": "Вы не являетесь участником этого чата."},
                            status=status.HTTP_403_FORBIDDEN)

        mutable_data = request.data.copy()
        mutable_data['chat'] = chat.pk

        serializer = MessageSerializer(data=mutable_data)
        if serializer.is_valid():
            serializer.save(chat=chat, sender=request.user)

            # ОНОВЛЮЄМО ВЛАСНУ КВИТАНЦІЮ ПРО ПРОЧИТАННЯ
            ReadReceipt.objects.update_or_create(
                chat=chat,
                user=request.user,
                defaults={'last_read_message': serializer.instance}
            )

            # channel_layer.send(group_name, ...)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ViewSet для создания сообщений (для тех, кто хочет использовать отдельный URL)
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.all()
    http_method_names = ['post', 'delete']

    def perform_create(self, serializer):
        chat = serializer.validated_data['chat']
        if self.request.user not in chat.participants.all():
            raise PermissionDenied("Вы не можете отправлять сообщения в этот чат.")

        serializer.save(sender=self.request.user)