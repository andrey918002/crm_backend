from channels.auth import AuthMiddlewareStack
from rest_framework.authtoken.models import Token
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs


@database_sync_to_async
def get_user_from_token(scope):
    """Шукає користувача за токеном, переданим у параметрах запиту WebSocket."""
    query_string = scope.get('query_string', b'').decode('utf-8')
    token_key = None

    # Використовуємо parse_qs для надійного парсингу параметрів запиту
    query_params = parse_qs(query_string)

    if 'token' in query_params:
        # 'token' - це список, беремо перший елемент
        token_key = query_params['token'][0]

    if token_key:
        try:
            # Шукаємо токен у базі даних
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            pass

    return AnonymousUser()


class TokenAuthMiddleware:
    """
    Проміжний шар, який аутентифікує користувача, використовуючи токен
    переданий через параметр запиту 'token' у WebSocket URL.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Отримуємо користувача асинхронно
        scope['user'] = await get_user_from_token(scope)
        return await self.inner(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    """Складає AuthMiddleware поверх TokenAuthMiddleware."""
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))