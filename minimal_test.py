import requests
import json

TOKEN = "ВАШ_ТОКЕН_MAX"
URL = "https://platform-api.max.ru/messages"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

# ID из вашего вебхука
SENDER = 5194550    # sender.user_id (кто написал)
RECIPIENT_CHAT = 253857436  # recipient.chat_id (чат бота)

# Тестируем минимальные структуры
tests = [
    ("user_id + text", {"user_id": SENDER, "text": "Hello from bot"}),
    ("chat_id + text", {"chat_id": RECIPIENT_CHAT, "text": "Hello via chat_id"}),
    ("user_id + text (str)", {"user_id": str(SENDER), "text": "Hello string id"}),
]

print("🔍 Минимальный тест структуры...\n")
for name, payload in tests:
    try:
        r = requests.post(URL, headers=HEADERS, json=payload, timeout=10)
        ok = r.status_code == 200 and not r.text.strip().startswith('{"code"')
        print(f"[{'✅' if ok else '❌'}] {name}")
        print(f"    📤 {json.dumps(payload)}")
        print(f"    📥 {r.status_code} | {r.text[:120]}\n")
        if ok:
            print(f"🎉 УСПЕХ! Используйте эту структуру в боте.")
            break
    except Exception as e:
        print(f"[💥] {name} | {e}\n")