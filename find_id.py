import requests
import json

TOKEN = "ВАШ_ТОКЕН_MAX"
BASE = "https://platform-api.max.ru"
CHAT_ID = 253857436
USER_ID = 5194550

# Базовое тело сообщения
BASE_MSG = {"body": {"text": "Test", "format": "plain"}}

variants = [
    {"peer_id": CHAT_ID, **BASE_MSG},                     # 1. peer_id (число)
    {"chat_id": str(CHAT_ID), **BASE_MSG},                # 2. chat_id (строка)
    {"user_id": str(USER_ID), **BASE_MSG},                # 3. user_id (строка)
    {"recipient": {"chat_id": CHAT_ID}, **BASE_MSG},      # 4. recipient.chat_id
    {"to": {"user_id": USER_ID}, **BASE_MSG}              # 5. to.user_id
]

for i, payload in enumerate(variants, 1):
    print(f"\n🔍 Тест {i}: {list(payload.keys())[0]} = {list(payload.values())[0]}")
    try:
        r = requests.post(f"{BASE}/messages", headers={"Authorization": TOKEN, "Content-Type": "application/json"}, json=payload, timeout=10)
        print(f"   📥 HTTP {r.status_code} | {r.text[:100]}")
        if r.status_code == 200 and not r.text.startswith('{"code"'):
            print("   ✅ УСПЕХ! Сообщение должно прийти в MAX.")
    except Exception as e:
        print(f"   ❌ {e}")