# chat/permissions.py
from rest_framework import permissions


class IsParticipant(permissions.BasePermission):
    """
    Разрешение только для пользователей, которые являются участниками чата.
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем GET, POST, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated and request.user in obj.participants.all()

        # Для изменения (PUT/PATCH/DELETE) разрешаем, если пользователь - участник
        return request.user.is_authenticated and request.user in obj.participants.all()

# Разрешение, чтобы только авторизованные могли создавать/читать списки чатов/сообщений
# (Вам достаточно использовать permissions.IsAuthenticated в views.py)