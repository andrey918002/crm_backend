# tasks/permissions.py
from rest_framework import permissions


class IsAdminOrEditor(permissions.BasePermission):
    """Разрешение только для Администраторов и Редакторов."""

    def has_permission(self, request, view):
        # Если пользователя нет (не авторизован)
        if not request.user.is_authenticated:
            return False

        # Предполагается, что у пользователя есть поле 'role'
        user_role = getattr(request.user, 'role', 'guest')
        return user_role in ['admin', 'editor']


class IsAssignedUserOrAdmin(permissions.BasePermission):
    """Разрешение для администратора или назначенного пользователя на уровне объекта."""

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin/Editor имеет полный доступ
        if getattr(user, 'role', 'guest') in ['admin', 'editor']:
            return True

        # Безопасные методы (GET, HEAD, OPTIONS) разрешены всем авторизованным (или назначенным)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверяем, назначен ли пользователь на задачу
        return user in obj.assigned_to.all()