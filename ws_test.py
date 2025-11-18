import websocket
import json
import threading
import time

# --- НАЛАШТУВАННЯ ---
CHAT_ID = 1
AUTH_TOKEN = "ac0636c4461385787c33d46ccd4f6df6313df057" # Ваш токен
WS_URL = f"ws://127.0.0.1:8000/ws/chat/{CHAT_ID}/?token={AUTH_TOKEN}"
# --------------------

def on_message(ws, message):
    """Обробка отриманого повідомлення."""
    print(f"\n<<< ОТРИМАНО: {message}")

def on_error(ws, error):
    """Обробка помилок."""
    print(f"\n!!! ПОМИЛКА: {error}")

def on_close(ws, close_status_code, close_msg):
    """Обробка закриття з'єднання."""
    print(f"\n--- З'ЄДНАННЯ ЗАКРИТО (Код: {close_status_code}) ---")

def on_open(ws):
    """Обробка успішного відкриття з'єднання."""
    print(f"+++ З'ЄДНАННЯ ВІДКРИТО З {WS_URL} +++")

    def run(*args):
        # Надсилаємо перше повідомлення через 3 секунди
        time.sleep(3)
        test_message = {
            "content": "Це тестове повідомлення з Python-скрипта."
        }

        print(f"\n>>> ВІДПРАВЛЕНО: {test_message}")
        ws.send(json.dumps(test_message))

        # Залишаємо з'єднання відкритим на 5 секунд для отримання відповіді
        time.sleep(5)
        ws.close()

    # Запускаємо надсилання повідомлення в окремому потоці, щоб не блокувати головний
    threading.Thread(target=run).start()

# --- ОСНОВНИЙ ЦИКЛ З'ЄДНАННЯ ---
if __name__ == "__main__":
    print(f"Спроба підключення до: {WS_URL}")

    # Встановлюємо налаштування для WebSocket
    ws = websocket.WebSocketApp(WS_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    # Запускаємо постійний цикл WebSocket
    # Зауважте: ws.run_forever() блокує.
    ws.run_forever()