from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Администратор"
        EDITOR = "editor", "Редактор"
        USER = "user", "Пользователь"
        GUEST = "guest", "Гость"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.GUEST,
        verbose_name="Роль"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

