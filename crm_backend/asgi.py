# crm_backend/asgi.py

import os

# 1. Встановлюємо змінну оточення DJANGO_SETTINGS_MODULE ПЕРЕД УСІМА ІМПОРТАМИ.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_backend.settings')

# 2. Імпортуємо get_asgi_application тільки після встановлення змінної оточення.
from django.core.asgi import get_asgi_application

# Це ініціалізує Django та його налаштування для HTTP-трафіку.
django_asgi_app = get_asgi_application()

# 3. Тепер ми можемо безпечно імпортувати код, що залежить від налаштувань (Token, models, etc.).
from channels.routing import ProtocolTypeRouter, URLRouter
from chat import routing
from accounts.middleware import TokenAuthMiddlewareStack  # Тепер цей імпорт безпечний!

application = ProtocolTypeRouter({
    # Обробляє стандартні HTTP-запити (DRF, адмін-панель)
    "http": django_asgi_app,

    # Обробляє WebSocket-запити
    "websocket": TokenAuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})