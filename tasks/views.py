# tasks/views.py
from rest_framework import viewsets, generics, permissions
from .models import Task, Status, TimeEntry
from .serializers import TaskSerializer, StatusSerializer, TimeEntrySerializer
from .permissions import IsAdminOrEditor, IsAssignedUserOrAdmin
from rest_framework.exceptions import PermissionDenied


# -------------------- 1. Статусы (Колонки) --------------------

class StatusListView(generics.ListAPIView):
    """Возвращает список всех статусов для построения доски."""
    queryset = Status.objects.all().order_by('order')
    serializer_class = StatusSerializer
    permission_classes = [permissions.IsAuthenticated]


# -------------------- 2. Задачи (Task) --------------------

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Фильтрация задач по ролям."""
        user = self.request.user
        if user.role in ['admin', 'editor']:
            # Администраторы и редакторы видят все задачи
            return Task.objects.all()
        # Обычные пользователи видят только те, на которые назначены
        return Task.objects.filter(assigned_to=user).distinct()

    def get_permissions(self):
        """Определяет разрешения в зависимости от действия."""
        if self.action in ['create', 'destroy']:
            # Создавать и удалять могут только Admin/Editor
            permission_classes = [IsAdminOrEditor]
        elif self.action in ['update', 'partial_update']:
            # Обновлять могут Admin/Editor ИЛИ назначенный пользователь
            permission_classes = [IsAssignedUserOrAdmin]
        else:
            # Читать могут все авторизованные (get_queryset отфильтрует, что именно)
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # При создании автоматически устанавливаем создателя
        serializer.save(creator=self.request.user)


# -------------------- 3. Учет времени (TimeEntry) --------------------

class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Убеждаемся, что пользователь, который трекает время, назначен на задачу
        task = serializer.validated_data['task']
        user = self.request.user

        if user not in task.assigned_to.all() and user.role not in ['admin', 'editor']:
            raise PermissionDenied("Вы не назначены на эту задачу и не имеете прав администратора.")

        # Автоматически устанавливаем пользователя, который создал запись времени
        serializer.save(user=user)
