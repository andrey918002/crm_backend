# chat/routing.py
from django.urls import re_path
from . import consumers # Буде створено наступним кроком

websocket_urlpatterns = [
    # Відстежуємо URL: ws/chat/1/, ws/chat/2/, і т.д.
    re_path(r'ws/chat/(?P<chat_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]