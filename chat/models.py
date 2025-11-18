# chat/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


# 1. Модель Чат-Кімнати
class Chat(models.Model):
    """
    Модель для чат-кімнати (приватної або групової).
    """
    participants = models.ManyToManyField(User, related_name='chats', verbose_name="Участники")
    is_group_chat = models.BooleanField(default=False, verbose_name="Групповой чат")
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name="Название чата")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        # Гарантуємо унікальність приватної розмови між двома користувачами (потрібна буде додаткова логіка у View)

    def __str__(self):
        if self.title:
            return self.title
        # Для приватного чату повертаємо імена учасників
        return f"Чат с: {', '.join([user.username for user in self.participants.all()])}"


# 2. Модель Повідомлення
class Message(models.Model):
    """
    Модель для одного сообщения.
    """
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages', verbose_name="Чат")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Отправитель")
    content = models.TextField(verbose_name="Содержание")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} ({self.chat.id}): {self.content[:30]}..."


# 3. Модель Квитанції про Прочитання (для сповіщень)
class ReadReceipt(models.Model):
    """
    Отслеживает последнее прочитанное сообщение в чате для каждого пользователя.
    Используется для определения количества непрочитанных сообщений.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_receipts', verbose_name="Пользователь")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='read_receipts', verbose_name="Чат")
    last_read_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True,
                                          verbose_name="Последнее прочитанное сообщение")

    class Meta:
        verbose_name = "Квитанция о прочтении"
        verbose_name_plural = "Квитанции о прочтении"
        unique_together = ('user', 'chat')  # Один пользователь может иметь только один статус прочтения для одного чата

    def __str__(self):
        return f"Пользователь {self.user.username} прочитал до: {self.last_read_message or 'Нет'}"
