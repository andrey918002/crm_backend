# accounts/urls.py
from django.urls import path
from .views import RegisterView, CustomObtainAuthToken, ProfileView, LogoutView

urlpatterns = [
    # Регистрация нового пользователя
    path("register/", RegisterView.as_view(), name="register"),

    # Логин (получение токена)
    path("login/", CustomObtainAuthToken.as_view(), name="login"),

    # Логаут (удаление токена)
    path("logout/", LogoutView.as_view(), name="logout"),

    # Получение данных текущего пользователя
    path("profile/", ProfileView.as_view(), name="profile"),
]

