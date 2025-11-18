# tasks/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views  # Поки що цей файл може не існувати, але ми його створимо

router = DefaultRouter()
# Реєструємо TaskViewSet для роботи з задачами
router.register(r'tasks', views.TaskViewSet, basename='task')
# Реєструємо TimeEntryViewSet для роботи з часом
router.register(r'time_entries', views.TimeEntryViewSet, basename='time-entry')

urlpatterns = [
    # Ендпоїнт для отримання списку статусів
    path('statuses/', views.StatusListView.as_view(), name='status-list'),

    # Підключаємо роутер для TaskViewSet та TimeEntryViewSet
    path('', include(router.urls)),
]