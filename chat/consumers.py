import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Chat, Message, ReadReceipt  # Додано імпорт ReadReceipt

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        # Якщо користувач не автентифікований, закриваємо з'єднання
        if not self.user.is_authenticated:
            await self.close()
            return

        self.chat_group_names = []

        # Отримуємо ID чатів, у яких бере участь користувач
        chat_ids = await self.get_user_chat_ids(self.user)

        for chat_id in chat_ids:
            group_name = f'chat_{chat_id}'
            self.chat_group_names.append(group_name)
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )

        await self.accept()

    async def disconnect(self, close_code):
        for group_name in self.chat_group_names:
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Обробляє вхідні повідомлення з WebSocket.
        Підтримує команди 'send_message' та 'mark_as_read'.
        """
        data = json.loads(text_data)
        command = data.get('command')
        chat_id = data.get('chat_id')
        user = self.scope['user']

        if not user.is_authenticated:
            await self.close()
            return

        if command == 'send_message':
            message_content = data.get('content')
            await self.send_chat_message(chat_id, user.id, message_content)

        # 💡 НОВИЙ ОБРОБНИК: Позначення чату як прочитаного
        elif command == 'mark_as_read':
            if chat_id:
                # Викликаємо асинхронний метод, який оновлює базу даних
                await self.mark_chat_as_read(int(chat_id), user)

    async def chat_message(self, event):
        """
        Отримує повідомлення з групового каналу (channel_layer) та відправляє його на WS.
        """
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'chat_id': event['chat_id'],
            # Додайте інші поля, які вам потрібні
        }))

    # -----------------------------------------------------------
    # СИНХРОННІ МЕТОДИ (робота з базою даних)
    # -----------------------------------------------------------

    @database_sync_to_async
    def get_user_chat_ids(self, user):
        """Отримує ID усіх чатів, у яких бере участь користувач."""
        return list(Chat.objects.filter(participants=user).values_list('id', flat=True))

    @database_sync_to_async
    def create_message(self, chat_id, sender_id, content):
        """Створює нове повідомлення в базі даних."""
        try:
            chat = Chat.objects.get(pk=chat_id)
            sender = User.objects.get(pk=sender_id)

            # Перевірка участі
            if sender not in chat.participants.all():
                return None

            message = Message.objects.create(chat=chat, sender=sender, content=content)

            # 💡 Автоматичне оновлення ReadReceipt для відправника
            ReadReceipt.objects.update_or_create(
                chat=chat,
                user=sender,
                defaults={'last_read_message': message}
            )

            return message

        except (Chat.DoesNotExist, User.DoesNotExist):
            return None

    async def send_chat_message(self, chat_id, sender_id, content):
        """Обробляє відправку повідомлення, створює його та розсилає."""
        message = await self.create_message(chat_id, sender_id, content)

        if message:
            group_name = f'chat_{chat_id}'

            # Підготовка даних для розсилки
            message_data = {
                'id': message.id,
                'chat': message.chat_id,
                'sender': {'id': message.sender.id, 'username': message.sender.username},
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
            }

            await self.channel_layer.group_send(
                group_name,
                {
                    'type': 'chat.message',
                    'message': message_data,
                    'sender': message.sender.username,  # Можна використовувати для відображення
                    'timestamp': message.timestamp.isoformat(),
                    'chat_id': chat_id,
                }
            )

    @database_sync_to_async
    def mark_chat_as_read(self, chat_id, user):
        """
        Синхронно знаходить чат та оновлює ReadReceipt для користувача.
        Викликається, коли користувач відкриває чат через WS.
        """
        try:
            chat = Chat.objects.get(pk=chat_id)

            # Перевіряємо, чи є користувач учасником
            if user not in chat.participants.all():
                return

            # Знаходимо останнє повідомлення в чаті
            # Використовуємо .messages, оскільки ми це виправили у models.py
            last_message = chat.messages.filter(sender__isnull=False).order_by('-timestamp').first()

            if last_message:
                # Створюємо або оновлюємо ReadReceipt
                ReadReceipt.objects.update_or_create(
                    chat=chat,
                    user=user,
                    defaults={'last_read_message': last_message}
                )

        except Chat.DoesNotExist:
            pass