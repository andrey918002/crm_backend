# tasks/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

# Получаем модель пользователя
User = settings.AUTH_USER_MODEL


# -------------------------------------------------------------
# ⚠️ ФУНКЦІЯ ДЛЯ СЕРІАЛІЗАЦІЇ СТАТУСУ ЗА ЗАМОВЧУВАННЯМ
def get_default_status():
    """Возвращает объект статуса 'К выполнению' для использования в default."""
    try:
        # Пытаемся получить объект Status с title='TODO'
        return Status.objects.get(title='TODO')
    except ObjectDoesNotExist:
        # Если статус не найден (например, при первой миграции),
        # возвращаем None или первый созданный, чтобы избежать сбоя.
        # В реальной ситуации, если миграция 0001_initial еще не прошла,
        # этот код будет вызван на следующем шаге.
        # Для корректной работы в production Status.objects.get() должен быть уверен, что статус существует.
        # Для начальной миграции Django справится с чистым вызовом.
        pass


# -------------------------------------------------------------

# 1. Статусы задач (Колонки доски Trello)
class Status(models.Model):
    """Модель для колонок доски (К выполнению, Выполняется, Выполнено)."""
    TITLE_CHOICES = [
        ('TODO', 'К выполнению'),
        ('IN_PROGRESS', 'Выполняется'),
        ('DONE', 'Выполнено'),
        ('BLOCKED', 'Заблокировано'),
    ]
    title = models.CharField(max_length=50, choices=TITLE_CHOICES, unique=True)
    order = models.IntegerField(default=0)  # Для сортировки колонок

    class Meta:
        verbose_name_plural = "Статусы"

    def __str__(self):
        return self.get_title_display()


# 2. Модель задачи
class Task(models.Model):
    """Основная модель задачи."""
    title = models.CharField(max_length=255, verbose_name="Название задачи")
    description = models.TextField(blank=True, verbose_name="Описание")

    # Связи с пользователями
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                related_name='created_tasks', verbose_name="Создатель")
    assigned_to = models.ManyToManyField(User, related_name='assigned_tasks',
                                         verbose_name="Исполнители")

    # Статус и сроки. Используем функцию, которую Django может сериализовать.
    status = models.ForeignKey(Status, on_delete=models.PROTECT,
                               related_name='tasks', default=get_default_status)
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['due_date', 'created_at']

    def __str__(self):
        return self.title


# 3. Модель отслеживания времени (Time Tracking)
class TimeEntry(models.Model):
    """Модель для фиксации затраченного времени на задачу."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries',
                             verbose_name="Задача")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracked_time',
                             verbose_name="Пользователь")

    start_time = models.DateTimeField(default=timezone.now, verbose_name="Начало")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Окончание")

    duration = models.DurationField(null=True, blank=True, verbose_name="Длительность")

    class Meta:
        verbose_name = "Учет времени"
        verbose_name_plural = "Учет времени"

    def __str__(self):
        return f"{self.user.username} - {self.task.title}"

    # Переопределяем метод save для расчета длительности
    def save(self, *args, **kwargs):
        if self.start_time and self.end_time and not self.duration:
            self.duration = self.end_time - self.start_time
        super().save(*args, **kwargs)