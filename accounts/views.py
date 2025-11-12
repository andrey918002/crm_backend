## accounts/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  # Импорт парсеров
from django.contrib.auth import get_user_model, authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


# ---------------------- Регистрация ----------------------
@method_decorator(csrf_exempt, name='dispatch') # Отключаем CSRF для POST запросов
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer # Обязательно для CreateAPIView
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser] # Явно указываем парсеры для form-data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Получаем токен, который был создан в RegisterSerializer.create()
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "token": token.key
        }, status=status.HTTP_201_CREATED)


# ---------------------- Кастомный логин ----------------------
class CustomObtainAuthToken(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if username is None or password is None:
            return Response({"error": "Please provide username and password"},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"},
                            status=status.HTTP_400_BAD_REQUEST)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        })


# ---------------------- Профиль текущего пользователя ----------------------
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ---------------------- Логаут ----------------------
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Удаляем токен
        Token.objects.filter(user=request.user).delete()
        return Response({"success": "Logged out successfully"}, status=status.HTTP_200_OK)