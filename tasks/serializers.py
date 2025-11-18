from rest_framework import serializers
from .models import Task, Status, TimeEntry
from django.contrib.auth import get_user_model

# Получаем модель пользователя
User = get_user_model()


# --- Вспомогательные сериализаторы ---

class StatusSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения статусов (колонок)."""

    class Meta:
        model = Status
        fields = ['id', 'title', 'order']


class UserAssignedSerializer(serializers.ModelSerializer):
    """Спрощенный сериализатор для отображения назначенных пользователей (READ)."""

    class Meta:
        model = User
        fields = ['id', 'username']


# --- Основные сериализаторы ---

class TaskSerializer(serializers.ModelSerializer):
    # 1. Поле для ЧТЕНИЯ статуса (полный объект)
    status = StatusSerializer(read_only=True)

    # 2. Поле для ЗАПИСИ статуса (только ID, для PATCH/PUT)
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=Status.objects.all(), source='status', write_only=True, required=False
    )

    # 3. Поле для ЧТЕНИЯ назначенных пользователей (список объектов)
    assigned_to = UserAssignedSerializer(many=True, read_only=True)

    # 4. Поле для ЗАПИСИ назначенных пользователей (список ID)
    assigned_to_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True, required=False
    )

    # Поле создателя всегда только для чтения
    creator = UserAssignedSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'creator', 'status',
            'status_id', 'due_date', 'created_at',
            'assigned_to', 'assigned_to_ids'  # 'assigned_to_ids' используется при POST
        ]
        # Указываем, какие поля не могут быть изменены пользователем (кроме создателя, который устанавливается автоматически)
        read_only_fields = ['created_at']

    def create(self, validated_data):
        """Переопределяем создание для обработки ManyToManyField (assigned_to_ids)."""

        # 1. Извлекаем список ID исполнителей из данных
        assigned_to_ids = validated_data.pop('assigned_to_ids', None)

        # 2. Устанавливаем текущего пользователя как создателя
        validated_data['creator'] = self.context['request'].user

        # 3. Создаем объект Task (без ManyToMany полей)
        task = super().create(validated_data)

        # 4. Добавляем исполнителей, если они были переданы
        if assigned_to_ids is not None:
            task.assigned_to.set(assigned_to_ids)

        return task


# -------------------- 3. Модель отслеживания времени --------------------

class TimeEntrySerializer(serializers.ModelSerializer):
    user = UserAssignedSerializer(read_only=True)

    class Meta:
        model = TimeEntry
        # 'task' - ID задачи, на которую трекается время
        fields = ['id', 'task', 'user', 'start_time', 'end_time', 'duration']
        read_only_fields = ['user', 'duration']